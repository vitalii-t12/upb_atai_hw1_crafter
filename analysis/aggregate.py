#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge multiple runs under a logdir and export mean±std CSV plus a tiny table
with last-point scores for LaTeX \\input.
"""
import argparse
import pathlib
import pickle

import pandas as pd


def read_pkl(path):
    events = []
    with open(path, "rb") as f:
        while True:
            try:
                events.append(pickle.load(f))
            except EOFError:
                break
    return events


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--logdir", required=True, help="Folder with seed subfolders.")
    parser.add_argument("--out", default="report/figures/agent_agg.csv")
    args = parser.parse_args()

    indir = pathlib.Path(args.logdir)
    fns = sorted(indir.glob("**/*/eval_stats.pkl"))
    runs = []
    for i, fn in enumerate(fns):
        df = pd.DataFrame(read_pkl(fn))
        df["run"] = i
        runs.append(df)
    if not runs:
        raise FileNotFoundError(f"No eval_stats.pkl found under {indir}")

    # Clip to min length
    min_len = min(len(r) for r in runs)
    runs = [r.iloc[:min_len].copy() for r in runs]
    df = pd.concat(runs, ignore_index=True)

    g = df.groupby("step")["avg_return"]
    agg = pd.DataFrame({"step": g.mean().index.values, "mean": g.mean().values, "std": g.std().values, "n": g.count().values})
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    agg.to_csv(args.out, index=False)

    # final row for \\input
    last = agg.iloc[-1]
    tiny = pd.DataFrame(
        {"step": [int(last["step"])], "mean": [last["mean"]], "std": [last["std"]], "n": [int(last["n"])]}
    )
    tiny.to_csv(pathlib.Path(args.out).with_suffix(".final.csv"), index=False)
    print(f"Wrote {args.out} and {pathlib.Path(args.out).with_suffix('.final.csv')}")


if __name__ == "__main__":
    main()