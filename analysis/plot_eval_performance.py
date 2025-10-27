#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extended plotting:
- Accept multiple --logdir (each may contain multiple seed subfolders).
- Shade mean±std across seeds.
- Overlay random baseline and agent curves (legend from folder names).
- Save PNG+PDF to report/figures/ and export CSV.
"""
import argparse
import pathlib
import pickle
from typing import Dict, List

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def read_pkl(path):
    events = []
    with open(path, "rb") as f:
        while True:
            try:
                events.append(pickle.load(f))
            except EOFError:
                break
    return events


def runs_from_logdir(indir: pathlib.Path, clip: bool = True) -> pd.DataFrame:
    fns = sorted(list(indir.glob("**/*/eval_stats.pkl")))
    runs = []
    for idx, fn in enumerate(fns):
        df = pd.DataFrame(read_pkl(fn))
        df["run"] = idx
        runs.append(df)
    if not runs:
        raise FileNotFoundError(f"No eval_stats.pkl found under {indir}")
    if clip:
        min_len = min(len(r) for r in runs)
        runs = [r.iloc[:min_len].copy() for r in runs]
        print(f"[{indir.name}] Clipped all runs to {min_len} points.")
    df = pd.concat(runs, ignore_index=True)
    return df


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("step")["avg_return"]
    out = pd.DataFrame(
        {
            "step": g.mean().index.values,
            "mean": g.mean().values,
            "std": g.std().fillna(0.0).values,
            "n": g.count().values,
        }
    )
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--logdir", nargs="+", required=True, help="One or more folders to overlay.")
    parser.add_argument("--outdir", default="report/figures", help="Where to save figures and CSVs.")
    parser.add_argument("--no-clip", action="store_true", help="Do not clip runs to the shortest.")
    args = parser.parse_args()

    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(6, 4))
    for ld in args.logdir:
        p = pathlib.Path(ld)
        df = runs_from_logdir(p, clip=(not args.no-clip))
        agg = aggregate(df)
        label = p.name
        # Plot mean with shaded std
        sns.lineplot(x="step", y="mean", data=agg, label=label)
        plt.fill_between(agg["step"], agg["mean"] - agg["std"], agg["mean"] + agg["std"], alpha=0.15)

        # Export CSV for LaTeX
        csv_path = outdir / f"{label}_curve.csv"
        agg.to_csv(csv_path, index=False)
        # Save small final-score CSV row (last point)
        last = agg.iloc[-1:]
        last.assign(agent=label)[["agent", "step", "mean", "std", "n"]].to_csv(
            outdir / f"{label}_final.csv", index=False
        )

    plt.xlabel("step")
    plt.ylabel("avg_return")
    plt.title("Evaluation performance (mean ± std over seeds)")
    plt.tight_layout()
    png_path = outdir / "eval_curves.png"
    pdf_path = outdir / "eval_curves.pdf"
    plt.savefig(png_path, dpi=200)
    plt.savefig(pdf_path)
    print(f"Saved {png_path} and {pdf_path}")
    plt.show()


if __name__ == "__main__":
    main()