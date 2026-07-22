"""Sparse-checkout the GEM global exposure model summary CSVs.

The GEM repo is ~600 MB (mostly figures); the three per-country summary CSV
families we need total ~7 MB. A blob-filtered sparse checkout downloads only
those files and gives us the source commit SHA for provenance.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import config


@dataclass(frozen=True)
class SummaryFile:
    path: Path
    region: str   # e.g. "Oceania"
    country_dir: str  # e.g. "Vanuatu"
    kind: str     # Adm0 | Adm1 | Taxonomy


def _git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def ensure_gem_checkout(ref: str | None = None) -> str:
    """Clone or update the sparse GEM checkout; return the full commit SHA."""
    dest = config.GEM_CACHE
    if not (dest / ".git").exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        _git(
            "clone", "--depth", "1", "--filter=blob:none", "--sparse",
            config.GEM_REPO_URL, str(dest),
        )
        _git("sparse-checkout", "set", "--no-cone", *config.GEM_SPARSE_PATTERNS, cwd=dest)

    target = ref or "main"
    _git("fetch", "--depth", "1", "origin", target, cwd=dest)
    _git("checkout", "--force", "FETCH_HEAD", cwd=dest)
    return _git("rev-parse", "HEAD", cwd=dest)


def get_head() -> str:
    """Commit SHA of the existing checkout, without fetching."""
    return _git("rev-parse", "HEAD", cwd=config.GEM_CACHE)


def iter_summary_files(kind: str) -> list[SummaryFile]:
    """Per-country summary CSVs of one kind, excluding the World/ rollups.

    The glob requires <Region>/<Country>/summaries/<file> (four segments), so
    World/summaries/* never matches.
    """
    files = []
    for path in sorted(config.GEM_CACHE.glob(f"*/*/summaries/Exposure_Summary_{kind}.csv")):
        region_dir, country_dir = path.relative_to(config.GEM_CACHE).parts[:2]
        files.append(
            SummaryFile(
                path=path,
                region=region_dir.replace("_", " "),
                country_dir=country_dir,
                kind=kind,
            )
        )
    return files


if __name__ == "__main__":
    sha = ensure_gem_checkout()
    counts = {kind: len(iter_summary_files(kind)) for kind in ("Adm0", "Adm1", "Taxonomy")}
    print(f"GEM checkout at {sha}")
    print(f"Summary files: {counts}")
