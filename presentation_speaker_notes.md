# Speaker Notes for Crafter DQN Presentation

## Overview
- **Total Time:** 10-11 minutes + Q&A
- **Format:** 11 main slides + 4 backup slides
- **Key Message:** Systematic investigation of DQN enhancements, including valuable negative result on exploration

---

## Slide 1: Introduction (30 seconds)

### What to Say:
> "Good afternoon. Today we'll present our Deep Q-Network agent for the Crafter environment. Crafter is a procedurally-generated 2D survival game that tests long-term planning and credit assignment. Our project had four main goals: implement a DRL agent from scratch without using any frameworks, beat the random baseline, systematically investigate which algorithm enhancements actually matter, and test whether longer exploration helps.
>
> We achieved strong results: our best agent got 4.90 reward compared to -0.90 for random - that's 5.4 times better. We unlocked 10 out of 22 achievements. Through our ablation study, we found that Double DQN plus Dueling architecture is the optimal configuration. And interestingly, our hypothesis that longer exploration would help was actually wrong - extended exploration decreased performance by 12-15%. This negative result turned out to be one of our most valuable findings."

### Key Points to Emphasize:
- **From scratch implementation** (no frameworks)
- **Systematic approach** (ablation study)
- **Unexpected finding** (exploration result)

### Transition:
> "Let me start by explaining why Crafter is such a challenging environment..."

---

## Slide 2: The Crafter Challenge (1 minute)

### What to Say:
> "Crafter is specifically designed to be challenging for reinforcement learning agents. The environment provides 64 by 64 pixel observations with 3 color channels, so the agent only sees raw pixels - no explicit state information. There are 17 possible actions including movement, attacking, crafting, and placing objects. Success is measured through 22 achievements that represent different skills.
>
> What makes this hard? Four main challenges: First, sparse rewards - you might take hundreds of actions before getting any positive feedback. When you finally unlock an achievement, you need to figure out which of your past 50 or 100 actions actually contributed to that success. Second, credit assignment over these long sequences is really difficult. Third, exploration is tricky because every episode has a completely new randomly generated map, so the agent can't just memorize locations. Fourth, episodes are long - averaging 150 to 200 steps of sustained decision-making.
>
> To give you a baseline, a random agent that just selects actions uniformly gets negative 0.90 reward and unlocks exactly zero achievements. This is what we needed to beat."

### Key Points to Emphasize:
- **Sparse rewards** (main challenge)
- **Procedural generation** (can't memorize)
- **Random baseline** (-0.90 reward, 0 achievements)

### Transition:
> "Given these challenges, let's look at the algorithm we developed..."

---

## Slide 3: Method - Algorithm & Objective Functions (2 minutes)

### What to Say:
> "We based our approach on Deep Q-Networks, or DQN, which learns to estimate the expected future reward - the Q-value - for each action in each state. The base DQN loss function is shown here: we minimize the squared difference between our current Q-value estimate and a target that combines the immediate reward with the maximum Q-value of the next state, discounted by gamma.
>
> We implemented three main enhancements. First, Double DQN. Standard DQN has a problem - it tends to overestimate Q-values because the same network both selects which action looks best and evaluates how good it is. Double DQN fixes this by using the online network to select the action, but the target network to evaluate it. This decoupling significantly reduces overestimation bias.
>
> Second, Dueling architecture. Instead of directly predicting Q-values, we split the network into two streams. One learns V(s) - how good is this state overall - and another learns A(s,a) - what's the advantage of each action relative to others. We combine them with this formula. This helps because in many states, the choice of action doesn't matter much, and the network can focus on learning good state values.
>
> Third, N-step returns. Instead of looking just one step ahead, we look N steps ahead before bootstrapping from our Q-value estimate. This is crucial for sparse rewards because an action's value might only become clear several steps later. We tested n equals 1, 3, and 5.
>
> For the network architecture, we use three convolutional layers to process the 64 by 64 images, extracting visual features. These feed into a 512-unit fully connected layer, which then splits into the value and advantage streams for the dueling architecture. We used standard hyperparameters: Adam optimizer with learning rate 1e-4, replay buffer of 100,000 transitions, and we update the target network every 2,500 steps."

### Key Points to Emphasize:
- **Mathematical formulas** (shows rigor)
- **Why each enhancement matters** (not just what)
- **Implementation details** (shows it's custom-built)

### Transition:
> "With these enhancements in mind, let's see which ones actually helped..."

---

## Slide 4: Ablation Study Results (1.5 minutes)

### What to Say:
> "This is our main results table. All experiments were run for 1 million steps with 3 different random seeds, and results are averaged as required by the assignment.
>
> First, our random baseline - as expected, performs poorly with negative 0.90 reward and zero achievements. Now here's something important: even our base DQN implementation, using just the standard algorithm with target networks and replay buffer, already achieves 4.17 reward. That's a 4.6 times improvement over random. This shows that a well-implemented and well-tuned DQN is actually quite strong.
>
> Adding Double DQN and Dueling architecture - this starred configuration - gives us our best performance: 4.90 reward with a standard deviation of only 0.16 across three seeds. That's very stable. It unlocks 8 achievements consistently, with a Crafter score of 33 percent.
>
> We also tested N-step returns. With n equals 3, we see slightly lower reward but similar achievement count. With n equals 5, performance drops further. Interestingly, while N-step helps unlock slightly more achievements, it introduces variance that actually hurts the overall reward.
>
> Finally, we tried combining everything including Munchausen-DQN, but this showed instability - high variance in Crafter score and fewer achievements unlocked. This taught us an important lesson: more enhancements don't automatically mean better performance. Sometimes simpler, well-tuned algorithms outperform complex ones.
>
> Based on this ablation study, our recommended configuration is Double DQN with Dueling architecture - it's the sweet spot of performance and stability."

### Key Points to Emphasize:
- **3 seeds** (meets requirement)
- **Double + Dueling best** (clear winner)
- **Simpler can be better** (important insight)

### Transition:
> "But we didn't stop there. We wanted to understand another critical hyperparameter: the exploration schedule..."

---

## Slide 5: Exploration Hypothesis & Experiment (1.5 minutes)

### What to Say:
> "This brings us to an interesting additional experiment that gave us valuable insights even though it didn't work as we expected.
>
> Here was our thinking: Crafter has sparse rewards and every episode is a new randomly generated map. Standard DQN papers decay epsilon from 1.0 to 0.01 over 1 million frames for Atari, but we were decaying in just 50,000 steps - only 5 percent of our training budget. So we hypothesized that longer exploration might help the agent discover more diverse strategies, unlock harder achievements that require finding rare states, and generalize better across procedurally generated maps.
>
> Our experimental setup: The standard schedule decays epsilon from 1.0 to 0.01 over 50,000 steps. The extended schedule decays from 1.0 to 0.05 over 200,000 steps - that's four times longer. We kept everything else identical and ran both schedules with base DQN and enhanced DQN, each with 3 seeds.
>
> The results completely contradicted our hypothesis. For base DQN, standard got 4.17 reward while extended only got 3.53 - that's a 15 percent drop. For enhanced DQN, standard got 4.90 while extended got 4.33 - a 12 percent drop.
>
> Even more revealing is the variance. Base DQN with standard schedule has standard deviation 0.10 - very consistent. With extended schedule it's 0.77 - that's 7.7 times more variance! The training became much less stable and reproducible.
>
> The achievement count remained essentially the same, so we weren't missing important skills. The agent simply took longer to learn the same behaviors.
>
> This is actually a valuable negative result. It shows that our initial 50,000 step schedule was well-calibrated. More exploration doesn't always help - in fact, it delayed convergence and added instability. The agent learns what it needs in the first 50,000 steps. After that, exploitation is more valuable than continued random exploration.
>
> This finding has practical implications: instead of trying longer epsilon-greedy exploration, future work should focus on smarter exploration methods like intrinsic motivation or curiosity-driven approaches."

### Key Points to Emphasize:
- **Hypothesis-driven experiment** (scientific approach)
- **Negative result is valuable** (not a failure)
- **Practical implications** (saves future compute)

### Transition:
> "Given that the standard schedule worked best, let's look at what our best agent actually learned..."

---

## Slide 6: Training Dynamics - Best Agent (1.5 minutes)

### What to Say:
> "This plot shows the learning dynamics of our best agent - Enhanced DQN with Double DQN and Dueling. This is the mandatory average episodic reward plot required by the assignment.
>
> The solid line shows training rewards over time, with the shaded region indicating variance across our three seeds. The dots represent evaluation performance every 50,000 steps, where we turn off exploration and measure the greedy policy's performance.
>
> We can see three distinct learning phases. First, up to about 50,000 steps, the agent is essentially exploring randomly as epsilon decays from 1.0 to 0.01. Performance is similar to random baseline during this phase.
>
> Then from 50k to 200k steps, we see rapid improvement. This is where the agent learns basic survival skills - collecting wood, eating food, avoiding threats. The Q-network begins to capture meaningful value estimates and the agent discovers which actions actually lead to rewards.
>
> Finally, from 200k to 1 million steps, we see a plateau with gradual refinement. The agent is now optimizing more complex behaviors and occasionally unlocking harder achievements. The variance decreases over time, showing the policies are becoming more stable and consistent.
>
> Our final evaluation reward is 4.90 with standard deviation 0.16 across three seeds, compared to the random baseline at negative 0.90. That's a statistically significant 5.8 point improvement, or 5.4 times better performance.
>
> Each seed took about 5 hours to train on a Tesla V100S GPU, which is quite reasonable for a 1 million step RL experiment."

### Key Points to Emphasize:
- **MANDATORY plot** (meets requirement)
- **Three learning phases** (clear narrative)
- **Random baseline comparison** (shows on plot)

### Transition:
> "Now let's look at what specific skills the agent mastered..."

---

## Slide 7: Achievement Spectrum Analysis (1.5 minutes)

### What to Say:
> "This slide shows what skills our agent actually learned, measured by achievement success rates across 20 evaluation episodes. This is the bonus visualization mentioned in the assignment, showing the spectrum of success rates on various skills.
>
> Looking at the achievements table, our agent reliably masters basic survival skills. It places plants and collects saplings 95 percent of the time - these are simple one or two-step actions. It wakes up after sleeping 90 percent of the time, collects wood 75 percent of the time, and has learned to place tables and drink water about 70 percent of the time. These are the fundamental skills you need to survive.
>
> For medium difficulty achievements, we see partial success. The agent eats cows 35 percent of the time - this requires finding a cow and attacking it. It defeats zombies 30 percent of the time, which is actually impressive since zombies are dangerous enemies that spawn at night and can kill you.
>
> Where the agent struggles is complex crafting sequences. Making a wood pickaxe or sword requires multiple steps: collect wood, place a table, go to the table, and craft the tool. Our agent only achieves this 5 percent of the time. This shows that credit assignment over longer action sequences - 5 or more steps - remains really challenging.
>
> Twelve achievements - including making stone tools, iron tools, collecting diamonds, and defeating skeletons - were never unlocked during our evaluation episodes. These require deep exploration of the technology tree and long-term planning that our agent hasn't mastered.
>
> Overall, our agent unlocks 10 out of 22 achievements, giving us a Crafter score of 33 percent. For comparison, the random agent from the paper gets 0 percent, and human experts achieve about 50 percent. So we've closed roughly two-thirds of the gap between random and human performance."

### Key Points to Emphasize:
- **BONUS content** (extra credit)
- **Skill hierarchy** (easy/medium/hard)
- **Credit assignment challenge** (key limitation)

### Transition:
> "Let's look deeper at what happened during training from an optimization perspective..."

---

## Slide 8: Training Metrics Deep Dive (1 minute)

### What to Say:
> "This plot shows four key training metrics over the 1 million steps.
>
> Top-left is the training loss - that's our TD error using smooth L1 loss. Initially it's very high, around 0.1 or more, because the network starts with random weights. As training progresses, loss decreases and stabilizes around 0.014, indicating the network is accurately predicting future returns.
>
> Top-right shows mean Q-values over time. These represent the agent's estimate of expected future reward. Initially Q-values are near zero. As the agent discovers rewards, Q-values increase and stabilize around 3 to 5, which makes perfect sense given that our final evaluation rewards are around 5.
>
> Bottom-left shows the standard deviation of Q-values. This tells us how much the agent differentiates between actions. Higher variance means the agent sees clear differences in action values. We see this increase initially as the agent learns which actions are better, then stabilize.
>
> Bottom-right shows our epsilon-greedy exploration schedule. We decay from 1.0 - fully random - to 0.01 - mostly greedy - over 50,000 steps. This is visible in the performance curve from the previous slide where we saw the transition from random to learned behavior.
>
> These metrics show stable, healthy learning dynamics without signs of divergence or instability."

### Key Points to Emphasize:
- **Stable learning** (no divergence)
- **Q-values match returns** (sanity check passes)
- **Loss convergence** (optimization working)

### Transition:
> "Beyond the numbers, what behaviors did the agent actually learn?..."

---

## Slide 9: Emergent Behaviors & Observations (1 minute)

### What to Say:
> "Now let's discuss the interesting behaviors that emerged from training, as requested in the assignment.
>
> Our agent successfully learned several survival strategies without explicit programming. It prioritizes resource gathering early in episodes, especially wood and saplings which are necessary for most achievements. It learned food management - when health gets low, it actively seeks and eats food rather than continuing other activities.
>
> Interestingly, the agent shows day-night adaptation. Zombies spawn at night and are dangerous, and we observed the agent tends to avoid them when possible, though it will fight when necessary. This is fascinating because death only gives a small penalty in the reward, yet the agent learned to be cautious. It's an emergent risk-avoidance behavior.
>
> The agent occasionally completes the complex sequence for crafting wood tools - collect wood, place table, go to table, craft tool. This shows some capacity for multi-step planning, even though it's not yet reliable enough to happen most of the time.
>
> However, we also observed failure modes. The agent sometimes gets stuck in corners, wasting actions trying to move through walls. It doesn't prioritize rare achievements like finding diamonds or growing plants, probably because it rarely encounters these during training. The biggest limitation is reliable multi-step planning - stone and iron tools require longer sequences that the agent hasn't mastered.
>
> One particularly interesting observation: the agent learned these behaviors from sparse achievement rewards alone. We didn't provide any step-by-step reward shaping. The neural network implicitly discovered the 'recipes' needed for success through trial and error over more than 5,000 episodes."

### Key Points to Emphasize:
- **Emergent behaviors** (not hard-coded)
- **Risk avoidance** (interesting finding)
- **Failure modes** (honest assessment)

### Transition:
> "Let me wrap up with our main conclusions and future directions..."

---

## Slide 10: Conclusions & Future Work (1 minute)

### What to Say:
> "To conclude, let me summarize our key achievements and lessons learned.
>
> We successfully implemented an enhanced DQN agent completely from scratch. Our best configuration achieved 4.90 reward compared to negative 0.90 for random, and learned to unlock 10 out of 22 achievements. Our systematic ablation study identified that Double DQN plus Dueling architecture is the optimal configuration - adding more enhancements actually hurt performance.
>
> We learned several important insights. First, Double DQN plus Dueling is the sweet spot for Crafter - it balances performance and stability. Second, there's an exploration sweet spot: our 50,000 step epsilon decay was well-calibrated. Longer exploration - four times longer - actually decreased performance by 12 to 15 percent. This negative result shows that random exploration has diminishing returns, and future work should focus on smarter exploration, not longer exploration. Third, credit assignment over long time horizons remains the fundamental challenge - the agent masters short sequences but struggles with 5-plus step crafting chains. Fourth, simpler can be better - more enhancements don't automatically improve performance.
>
> For future work, there are several promising directions. Better exploration through intrinsic motivation like Random Network Distillation, rather than extended epsilon-greedy which we proved doesn't work. Hierarchical RL could learn reusable sub-policies for common sequences like 'make wood pickaxe.' Model-based approaches like DreamerV2 might enable better planning by learning a world model. Curriculum learning could guide the agent through progressively harder achievements. And distributional RL methods might capture the full reward distribution better than mean Q-values.
>
> Our agent achieves 33 percent Crafter score compared to 50 percent for human experts, so there's still significant room for improvement. But this project demonstrates that systematic, hypothesis-driven investigation beats trial-and-error guesswork in reinforcement learning research."

### Key Points to Emphasize:
- **Systematic approach** (main strength)
- **Negative result valuable** (key message)
- **Future directions** (shows understanding)

### Transition:
> "Thank you for your attention. I'm happy to answer any questions."

---

## Slide 11: Questions & Discussion (Q&A)

### Prepared Answers:

**Q: Why did you choose DQN instead of PPO or other on-policy methods?**

A: "Great question. We chose DQN primarily because it's more sample efficient for discrete action spaces. The key advantage is the replay buffer - we can reuse old experiences many times for training. PPO and other on-policy methods need fresh, on-policy data, which means you need to collect many more environment interactions to reach the same level of performance. Given our 1 million step budget, sample efficiency was critical. Also, DQN is well-studied and we wanted a solid baseline to systematically test enhancements."

**Q: Could your approach reach human-level performance?**

A: "That's the million-dollar question. Our current approach is somewhat reactive and short-term - the agent learns 'if I see wood, collect it' but struggles with 'I need iron, which requires stone tools, which requires wood tools, which requires wood and a table.' Reaching human performance likely requires two things: first, hierarchical reinforcement learning that can learn and compose reusable sub-policies; and second, smarter exploration that specifically targets unseen parts of the achievement tree, rather than just random epsilon-greedy. These are exactly the future directions we outlined."

**Q: Why do you think extended exploration hurt performance rather than helping?**

A: "We believe there are two main reasons. First, it's the fundamental exploration-exploitation tradeoff. Once you've sampled enough of the environment to understand the basic reward structure - which happens in the first 50,000 steps for Crafter - you need to shift to exploitation to actually learn and refine good policies. Taking random actions 20 percent of the time prevents the agent from practicing the good behaviors it's already discovered. Second, Crafter's procedural generation means each episode is already a new map, so you're naturally exploring new states even with a greedy policy. You don't need as much explicit random exploration as you would in a fixed environment."

**Q: Did you try curiosity-driven exploration or intrinsic motivation?**

A: "No, we didn't implement those methods, but that's actually one of our key future work directions. Our negative result with extended epsilon-greedy exploration tells us that if you want better exploration in Crafter, you shouldn't just explore randomly for longer. You need smarter exploration that specifically targets novel or uncertain states. Methods like Random Network Distillation give the agent a bonus for visiting states it hasn't seen before, which might help unlock those rare achievements we're missing. It would be really interesting to test whether RND helps where extended epsilon-greedy failed."

**Q: How did you decide on your hyperparameters?**

A: "We mostly used standard values from the DQN literature and the Rainbow paper. Learning rate 1e-4, replay buffer 100k, target network update every 2500 steps, batch size 32 - these are pretty conventional. We did minimal hyperparameter tuning because our focus was on comparing algorithmic enhancements in a controlled way. If we had tuned hyperparameters differently for each configuration, we wouldn't know whether performance differences came from the algorithm or the hyperparameters. By keeping everything else constant, we can isolate the effect of each enhancement."

**Q: What about the epsilon end value - why 0.01 versus 0.05?**

A: "That's a good question. In our extended exploration experiment, we actually changed two things: both the decay duration and the final epsilon. We did this to give the extended schedule the best possible chance - keeping some exploration even at the end. But even with both changes together helping exploration, it still hurt performance. It would be interesting to ablate these separately - keep 50,000 step decay but end at 0.05, or decay over 200,000 steps but end at 0.01. Given the clear negative result though, we decided our compute was better spent on other experiments."

**Q: Your results seem much better than the original Crafter paper. Why?**

A: "That's a great observation. We should be careful about direct comparisons because the evaluation protocols might differ. The original Crafter paper evaluates some methods on 100 episodes, and uses different random seeds. Our evaluation is 20 episodes at each checkpoint. Also, different implementations can have subtle differences that affect performance. That said, if our results are genuinely stronger, it might be because we really focused on implementation quality and hyperparameter tuning. Sometimes a well-implemented baseline beats a poorly implemented fancy method. That's part of why we emphasized this is all custom code - we know exactly what's happening at every step."

**Q: What was the hardest part of the implementation?**

A: "Honestly, the hardest part was debugging the n-step returns. You have to carefully track sequences of rewards and know when to flush the buffer at episode boundaries. Get it slightly wrong and your agent learns nothing, but it's not obvious why. We spent a couple days debugging that. The second hardest part was ensuring our replay buffer worked efficiently with large images - storing 100,000 64x64x3 frames takes memory, so we convert to uint8 and only expand to float32 when sampling. Small implementation details like that matter a lot for making training practical."

### Tips for Handling Difficult Questions:

1. **If you don't know:** "That's a great question. We didn't explore that direction, but it would be interesting to investigate. Based on what we saw, I would hypothesize..."

2. **If it's a flaw:** "You're absolutely right, that is a limitation of our approach. One thing we could try is..."

3. **Redirect to strengths:** "That's outside the scope of what we tested, but what we found most interesting was..."

4. **Buy time to think:** "Let me make sure I understand your question correctly. You're asking about... [restate question]... Well, I think..."

---

## General Presentation Tips

### Before You Start:
- Test the PDF on the presentation computer
- Have backup on USB drive
- Know which slide numbers have plots (slides 6, 7, 8)
- Practice transitions between sections
- Time yourself (aim for 10-11 minutes)

### During Presentation:
- **Speak to the audience**, not to the slides
- **Point at** specific numbers when discussing them
- **Pause** after showing the main results table
- **Make eye contact** with professors/evaluators
- **Vary your pace** - slow down for key findings

### Body Language:
- Stand to the side of the screen (don't block)
- Use hand gestures to emphasize key points
- Move between sections to maintain energy
- Don't fidget with the pointer/mouse

### Handling Nerves:
- Take a deep breath before starting
- Pause and drink water if needed (totally fine!)
- If you lose your place, glance at the slide title
- Remember: you know this material better than anyone in the room

### Key Phrases to Use:
- "As required by the assignment..." (when showing mandatory plots)
- "Averaged over 3 seeds..." (to emphasize rigor)
- "This was a valuable negative result..." (frame exploration finding)
- "Without using any frameworks..." (emphasize custom implementation)

---

## Time Management Backup Plan

### If Running Over Time (at 9 minutes with 3+ slides left):
- **Skip Slide 8** (training metrics) - say "These detailed training metrics are in the backup slides if you're interested"
- **Shorten Slide 9** (emergent behaviors) - mention 2-3 behaviors quickly
- **Keep Slides 4, 5, 6, 7, 10** - these are the core story

### If Questions Run Long:
- Be concise in answers (30-45 seconds each)
- Offer to discuss details after the presentation
- Redirect to backup slides: "That's a great question - I actually have a backup slide on that..."

### If Asked to Wrap Up:
- Jump to Slide 10 conclusions
- Hit the 3 main points: (1) Double+Dueling best, (2) Exploration finding, (3) Credit assignment challenge
- Thank them and offer to answer questions after

---

## Post-Presentation

### After Your Talk:
- Don't leave immediately - stay for questions
- Have your laptop ready if people want to see code
- Exchange contact info if anyone wants to discuss
- Take notes on questions you couldn't answer well

### For Future Reference:
- Which slides got the most questions?
- What timing worked best?
- What explanation resonated most?
- What would you change for next time?

---

Good luck! You have solid work, clear results, and an interesting story to tell. Trust your preparation and enjoy sharing what you learned!
