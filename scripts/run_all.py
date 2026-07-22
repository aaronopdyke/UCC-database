"""Run the full UCC-database pipeline.

Order: fetch GEM + compile UCC CSVs -> (optionally) rebuild boundaries from the
World Bank source -> emit site data (which also refreshes the UCC values baked
into the committed boundary TopoJSONs).

Typical uses:
  py scripts/run_all.py                     # data refresh (no geometry rebuild)
  py scripts/run_all.py --with-boundaries   # full rebuild incl. WB boundaries
  py scripts/run_all.py --skip-fetch        # reuse the cached GEM checkout
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def run(script: str, *args: str) -> None:
    print(f"\n=== {script} {' '.join(args)} ===")
    subprocess.run([sys.executable, str(SCRIPTS / script), *args], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-fetch", action="store_true",
                        help="reuse the cached GEM checkout as-is")
    parser.add_argument("--gem-ref", default=None,
                        help="GEM commit/branch to build from")
    parser.add_argument("--with-boundaries", action="store_true",
                        help="also rebuild boundary TopoJSONs from the WB source")
    args = parser.parse_args()

    ucc_args = ["--skip-fetch"] if args.skip_fetch else []
    if args.gem_ref:
        ucc_args += ["--gem-ref", args.gem_ref]
    run("build_ucc.py", *ucc_args)
    if args.with_boundaries:
        run("build_boundaries.py")
    run("build_site_data.py")
    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
