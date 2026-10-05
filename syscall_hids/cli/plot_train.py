"""
Training curves from a JSONL metrics file (like mace/cli/visualise_train.py).

Usage:
    hids-plot-train --results results/hids_PHP_CWE-434_run-123_train.txt
    hids-plot-train --results results/hids_PHP_CWE-434_run-123_train.txt --out plots/curves.png
"""

import argparse
import os

from syscall_hids.tools.visualization import plot_from_results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", required=True, help="JSONL metrics file from hids-train ({results_dir}/..._train.txt)")
    parser.add_argument("--out", default=None, help="Where to save the png (default: next to --results)")
    args = parser.parse_args()

    out_path = args.out or os.path.splitext(args.results)[0] + "_curves.png"
    if plot_from_results(args.results, out_path) is None:
        raise SystemExit(f"{args.results} has no mode=eval records, nothing to plot")
    print(f"Training curves saved to {out_path}")


if __name__ == "__main__":
    main()
