#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crafter QR-DQN training script.
- Keeps the original eval logging format (eval_stats.pkl).
- Defaults are the best hyperparameters found for this implementation.
- Uses GPU if available.
"""
import argparse
import pickle
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import torch
import torch.nn.functional as F

from src.crafter_wrapper import Env
from src.utils.seed import set_seed_everywhere
from src.utils.schedule import LinearSchedule, CosineSchedule
from src.agent.dqn_model import QRDuelingDQN
from src.agent.replay_buffer import PrioritizedReplayBuffer, NStepAdder
from src.agent.learner import quantile_huber_loss
from src.agent.policy import GreedyPolicy, EpsGreedyPolicy


def _save_stats(episodic_returns, crt_step, path):
    episodic_returns = torch.tensor(episodic_returns)
    avg_return = episodic_returns.mean().item()
    print(
        "[{:06d}] eval results: R/ep={:03.2f}, std={:03.2f}.".format(
            crt_step, avg_return, episodic_returns.std().item()
        )
    )
    with open(path + "/eval_stats.pkl", "ab") as f:
        pickle.dump({"step": crt_step, "avg_return": avg_return}, f)


@torch.no_grad()
def eval(agent: torch.nn.Module, env: Env, crt_step: int, opt) -> None:
    """Greedy evaluation; no epsilon."""
    agent.eval()
    episodic_returns = []
    greedy = GreedyPolicy(agent, opt.num_actions, opt.quantiles, device=opt.device)
    for _ in range(opt.eval_episodes):
        obs, done = env.reset(), False
        episodic_returns.append(0.0)
        while not done:
            action = greedy.act(obs)
            obs, reward, done, info = env.step(action)
            episodic_returns[-1] += reward
    _save_stats(episodic_returns, crt_step, opt.logdir)
    agent.train()


def _info(opt):
    try:
        int(opt.logdir.split("/")[-1])
    except Exception:
        print(
            "Warning, logdir path should end in a number indicating a separate "
            "training run, else the results might be overwritten."
        )
    if Path(opt.logdir).exists():
        print("Warning! Logdir path exists, results can be corrupted.")
    print(f"Saving results in {opt.logdir}.")
    print(
        f"Observations are of dims ({opt.history_length},84,84) with values in [0,1]. "
        "Frame stacking handled by the provided wrapper."
    )


def build_optimizer(net: torch.nn.Module, lr: float) -> torch.optim.Optimizer:
    return torch.optim.Adam(net.parameters(), lr=lr, eps=1e-4)


def compute_targets(
    rewards: torch.Tensor,
    dones: torch.Tensor,
    gamma: float,
    next_dist: torch.Tensor,
) -> torch.Tensor:
    """
    n-step bootstrapped targets for QR-DQN.
    rewards: [B]
    dones:   [B] (1 if terminal at n-step boundary)
    next_dist: [B, Ntau] distribution (already gathered w.r.t. argmax_a Q_online)
    returns target_z: [B, Ntau]
    """
    # When done, we should not bootstrap
    not_done = (1.0 - dones.float()).unsqueeze(1)  # [B,1]
    target = rewards.unsqueeze(1) + gamma * not_done * next_dist
    return target


def main(opt):
    _info(opt)
    set_seed_everywhere(opt.seed)

    # --- Device & envs
    opt.device = torch.device("cuda" if (torch.cuda.is_available() and not opt.cpu) else "cpu")
    torch.backends.cudnn.benchmark = True
    env = Env("train", opt)
    eval_env = Env("eval", opt)
    opt.num_actions = env.action_space.n

    # --- Networks
    online = QRDuelingDQN(
        in_channels=opt.history_length, num_actions=opt.num_actions, num_quantiles=opt.quantiles
    ).to(opt.device)
    target = QRDuelingDQN(
        in_channels=opt.history_length, num_actions=opt.num_actions, num_quantiles=opt.quantiles
    ).to(opt.device)
    target.load_state_dict(online.state_dict())
    optimizer = build_optimizer(online, opt.lr)

    # --- Replay & n-step
    replay = PrioritizedReplayBuffer(
        capacity=opt.replay_size,
        obs_shape=(opt.history_length, 84, 84),
        alpha=opt.prior_alpha,
        beta_start=opt.prior_beta_start,
        beta_frames=opt.prior_beta_frames,
        device=opt.device,
        store_uint8=True,
    )
    nstep_adder = NStepAdder(n=opt.n_step, gamma=opt.gamma)

    # --- Exploration schedule
    if opt.eps_schedule == "linear":
        eps_sched = LinearSchedule(opt.eps_start, opt.eps_end, opt.eps_decay_steps)
    else:
        eps_sched = CosineSchedule(opt.eps_start, opt.eps_end, opt.eps_decay_steps)

    # --- Policies
    behavior = EpsGreedyPolicy(
        net=online, num_actions=opt.num_actions, num_quantiles=opt.quantiles, schedule=eps_sched, device=opt.device
    )
    greedy_eval = GreedyPolicy(online, opt.num_actions, opt.quantiles, device=opt.device)

    # --- Main loop
    Path(opt.logdir).mkdir(parents=True, exist_ok=True)
    step_cnt, ep_cnt, done = 0, 0, True
    obs = None

    # Warmup: fill some experience (with epsilon=1 behavior inside policy)
    while replay.size < opt.warmup_steps:
        if done:
            ep_cnt += 1
            obs, done = env.reset(), False
            nstep_adder.reset(obs)
        action = behavior.act(obs, force_random=True)  # random during warmup
        next_obs, reward, done, info = env.step(action)
        ready = nstep_adder.add(action, reward, next_obs, done)
        if ready is not None:
            # (obs0, action, Rn, next_obs_n, done_n)
            o0, a0, Rn, on, dn = ready
            replay.add(o0, a0, Rn, on, dn)
        obs = next_obs

    # Training
    losses_moving = []
    while step_cnt < opt.steps:
        if done:
            ep_cnt += 1
            obs, done = env.reset(), False
            nstep_adder.reset(obs)

        # --- Act & step
        action = behavior.act(obs)
        next_obs, reward, done, info = env.step(action)
        ready = nstep_adder.add(action, reward, next_obs, done)
        if ready is not None:
            o0, a0, Rn, on, dn = ready
            replay.add(o0, a0, Rn, on, dn)
        obs = next_obs

        # --- Learn
        if step_cnt % opt.train_every == 0:
            batch = replay.sample(opt.batch_size)
            loss, td_errors = learn_qr_dqn(
                batch=batch,
                online=online,
                target=target,
                optimizer=optimizer,
                gamma=opt.gamma ** opt.n_step,  # since n-step target
                quantiles=opt.quantiles,
                kappa=opt.huber_kappa,
                double_dqn=True,
                grad_norm_clip=opt.grad_clip,
            )
            replay.update_priorities(batch["indices"], td_errors)
            losses_moving.append(loss)

        # --- Target updates
        if (step_cnt + 1) % opt.target_update_interval == 0:
            target.load_state_dict(online.state_dict())

        # --- Evaluation
        if (step_cnt + 1) % opt.eval_interval == 0:
            eval(online, eval_env, step_cnt + 1, opt)

        step_cnt += 1

    # One last eval at the very end if not aligned with interval
    if step_cnt % opt.eval_interval != 0:
        eval(online, eval_env, step_cnt, opt)


def learn_qr_dqn(
    batch: Dict[str, torch.Tensor],
    online: torch.nn.Module,
    target: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    gamma: float,
    quantiles: int,
    kappa: float,
    double_dqn: bool = True,
    grad_norm_clip: float = 10.0,
) -> Tuple[float, np.ndarray]:
    """
    One optimization step of QR-DQN with Double DQN target selection.
    batch contains:
        obs:  [B, C, 84, 84] float32 in [0,1]
        actions: [B] long
        rewards: [B] float
        next_obs: [B, C, 84, 84]
        dones: [B] float (1 if terminal)
        weights: [B] importance-sampling weights
        indices: [B] positions in replay
    Returns (scalar loss, |td_error| for PER)
    """
    obs = batch["obs"]
    actions = batch["actions"].long()
    rewards = batch["rewards"]
    next_obs = batch["next_obs"]
    dones = batch["dones"]
    isw = batch["weights"].unsqueeze(1)  # [B,1]

    B = obs.size(0)

    # Current quantile distributions Z_theta(s,a) -> [B, A, N]
    dist_all = online(obs)  # [B, A, N]
    # Gather chosen actions
    action_index = actions.view(B, 1, 1).expand(B, 1, quantiles)
    dist = dist_all.gather(1, action_index).squeeze(1)  # [B, N]

    with torch.no_grad():
        # Next action selection (Double DQN): argmax_a E[Z_online]
        next_dist_online = online(next_obs)  # [B, A, N]
        q_next_mean = next_dist_online.mean(dim=2)  # [B, A]
        next_actions = q_next_mean.argmax(dim=1, keepdim=True)  # [B,1]

        # Next distribution from target network at the selected actions
        next_dist_target = target(next_obs)  # [B, A, N]
        next_dist = next_dist_target.gather(1, next_actions.unsqueeze(2).expand(-1, -1, quantiles)).squeeze(1)  # [B,N]

        # n-step bootstrapped targets per quantile
        target_dist = compute_targets(rewards, dones, gamma, next_dist)  # [B, N]

    # Quantile Huber regression loss (Distributional RL)
    loss_per_item, td_abs = quantile_huber_loss(dist, target_dist, kappa=kappa)
    loss = (loss_per_item * isw).mean()

    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(online.parameters(), grad_norm_clip)
    optimizer.step()

    return loss.item(), td_abs.detach().cpu().numpy()


def get_options():
    """
    Extend the starter parser with our agent hyperparameters.
    Defaults = best hyperparameters for full run (per brief).
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--logdir", default="logdir/qr_dqn/0", help="logdir/agent_name/<seed>")
    parser.add_argument(
        "--steps", type=int, metavar="STEPS", default=1_000_000, help="Total number of training steps."
    )
    parser.add_argument(
        "-hist-len", "--history-length", default=4, type=int, help="Number of stacked frames in observation."
    )
    parser.add_argument(
        "--eval-interval", type=int, default=25_000, metavar="STEPS", help="Training steps between evaluations."
    )
    parser.add_argument("--eval-episodes", type=int, default=20, metavar="N", help="Eval episodes to average.")
    parser.add_argument("--cpu", action="store_true", help="Force CPU even if CUDA is available.")
    parser.add_argument("--seed", type=int, default=0)

    # --- Algorithm hyperparams (tuned defaults)
    parser.add_argument("--lr", type=float, default=2.5e-4)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--n-step", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--train-every", type=int, default=1)
    parser.add_argument("--target-update-interval", type=int, default=10_000)
    parser.add_argument("--grad-clip", type=float, default=10.0)
    parser.add_argument("--quantiles", type=int, default=51)
    parser.add_argument("--huber-kappa", type=float, default=1.0)

    # --- Replay (PER)
    parser.add_argument("--replay-size", type=int, default=250_000)
    parser.add_argument("--warmup-steps", type=int, default=20_000)
    parser.add_argument("--prior-alpha", type=float, default=0.6)
    parser.add_argument("--prior-beta-start", type=float, default=0.4)
    parser.add_argument("--prior-beta-frames", type=int, default=1_000_000)

    # --- Exploration
    parser.add_argument("--eps-start", type=float, default=1.0)
    parser.add_argument("--eps-end", type=float, default=0.01)
    parser.add_argument("--eps-decay-steps", type=int, default=800_000)
    parser.add_argument("--eps-schedule", choices=["linear", "cosine"], default="cosine")

    return parser.parse_args()


if __name__ == "__main__":
    main(get_options())
