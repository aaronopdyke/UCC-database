"""Compile the three UCC lists (ADM0, ADM1, taxonomy) from GEM summary CSVs.

UCC (unit construction cost, USD/m2) is always recomputed as
BLDG_REPL_COST_USD / TOTAL_AREA_SQM — the definition GEM uses for its
AVG_BLDG_COST_PER_AREA_USD column (structural + nonstructural, excluding
contents) — so that the computed TOTAL-occupancy rows are consistent with the
per-occupancy rows. The GEM column is still read and used as a cross-check.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

import pandas as pd
import requests

import config
from fetch_gem import ensure_gem_checkout, get_head, iter_summary_files

SOURCE_UCC = "AVG_BLDG_COST_PER_AREA_USD"

# Identity columns per summary family, in output order (after REGION).
ID_COLS = {
    "Adm0": ["ID_0", "NAME_0", "OCCUPANCY"],
    "Adm1": ["ID_0", "NAME_0", "ID_1", "NAME_1", "OCCUPANCY"],
    "Taxonomy": ["ID_0", "NAME_0", "OCCUPANCY", "MACRO_TAXONOMY", "TAXONOMY", "SETTLEMENT"],
}
# Grouping keys for the computed TOTAL-occupancy rows (ADM0/ADM1 only).
TOTAL_KEYS = {
    "Adm0": ["REGION", "ID_0", "NAME_0"],
    "Adm1": ["REGION", "ID_0", "NAME_0", "ID_1", "NAME_1"],
}
SORT_COLS = {
    "Adm0": ["NAME_0", "OCCUPANCY"],
    "Adm1": ["NAME_0", "NAME_1", "OCCUPANCY"],
    "Taxonomy": ["NAME_0", "OCCUPANCY", "MACRO_TAXONOMY", "TAXONOMY", "SETTLEMENT"],
}


def load_family(kind: str) -> pd.DataFrame:
    files = iter_summary_files(kind)
    if not files:
        sys.exit(f"No GEM summary files found for {kind}; run the fetch step first.")
    needed = ID_COLS[kind] + config.MEASURES
    frames = []
    for f in files:
        df = pd.read_csv(f.path, encoding="utf-8")
        if "COST_CONTENTS_USD" not in df.columns:  # tolerated: contents shown blank
            df["COST_CONTENTS_USD"] = 0
        missing = [c for c in needed if c not in df.columns]
        if missing:
            sys.exit(f"{f.path}: missing expected columns {missing}")
        if SOURCE_UCC not in df.columns:
            df[SOURCE_UCC] = pd.NA
        df = df[needed + [SOURCE_UCC]].copy()
        df.insert(0, "REGION", f.region)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def aggregate_taxonomy(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse rows that share a GEM taxonomy string.

    In the USA, Canada and US territories GEM keeps one row per HAZUS
    sub-occupancy (e.g. RES3A/RES3B/RES3C) for the same TAXONOMY string. Our
    list is keyed by the GEM taxonomy string, so those rows are summed and UCC
    becomes the area-weighted average. The GEM cross-check column is kept only
    for groups that were a single source row.
    """
    keys = ["REGION"] + ID_COLS["Taxonomy"]
    agg = df.groupby(keys, as_index=False, sort=False).agg(
        **{m: (m, "sum") for m in config.MEASURES},
        _n=("TAXONOMY", "size"),
        _src=(SOURCE_UCC, "first"),
    )
    agg[SOURCE_UCC] = agg["_src"].where(agg["_n"] == 1)
    return agg.drop(columns=["_n", "_src"])


def add_total_rows(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    totals = df.groupby(keys, as_index=False, sort=False)[config.MEASURES].sum()
    totals["OCCUPANCY"] = "TOTAL"
    totals[SOURCE_UCC] = pd.NA
    return pd.concat([df, totals], ignore_index=True)


def finalize(df: pd.DataFrame, kind: str, gem_commit: str) -> pd.DataFrame:
    df = df.copy()
    bad_occ = set(df["OCCUPANCY"].unique()) - set(config.OCCUPANCY_ORDER)
    assert not bad_occ, f"{kind}: unexpected OCCUPANCY values {bad_occ}"
    df["OCCUPANCY"] = pd.Categorical(
        df["OCCUPANCY"], categories=config.OCCUPANCY_ORDER, ordered=True
    )

    df["COST_CONTENTS_USD"] = df["COST_CONTENTS_USD"].fillna(0)
    for col in config.MEASURES:
        assert df[col].notna().all(), f"{kind}: NaN in {col}"
        df[col] = df[col].round().astype("int64")
    df[config.UCC_COL] = (
        (df["BLDG_REPL_COST_USD"] / df["TOTAL_AREA_SQM"])
        .where(df["TOTAL_AREA_SQM"] > 0)
        .round(1)
    )
    df[config.UCC_ADJ_COL] = df[config.UCC_COL]  # overwritten with CPI-adjusted values
    # contents cost per m2 mirrors the UCC definition; blank where GEM has none
    df[config.CONTENTS_COL] = (
        (df["COST_CONTENTS_USD"] / df["TOTAL_AREA_SQM"])
        .where((df["TOTAL_AREA_SQM"] > 0) & (df["COST_CONTENTS_USD"] > 0))
        .round(1)
    )

    df = df.sort_values(SORT_COLS[kind], kind="mergesort", ignore_index=True)
    df["GEM_COMMIT"] = gem_commit[:7]
    out_cols = ["REGION"] + ID_COLS[kind] + config.MEASURES + [
        config.UCC_COL, config.UCC_ADJ_COL, config.CONTENTS_COL, "GEM_COMMIT"]
    return df[out_cols + [SOURCE_UCC]]  # SOURCE_UCC kept for validation, dropped on write


def validate(adm0: pd.DataFrame, adm1: pd.DataFrame, tax: pd.DataFrame) -> dict:
    n_countries = adm0["ID_0"].nunique()
    assert n_countries >= 200, f"only {n_countries} countries — GEM checkout incomplete?"
    for name, df, keys in (
        ("adm0", adm0, ["ID_0", "OCCUPANCY"]),
        ("adm1", adm1, ["ID_0", "ID_1", "OCCUPANCY"]),
        ("taxonomy", tax, ["ID_0", "OCCUPANCY", "TAXONOMY", "SETTLEMENT"]),
    ):
        dupes = df.duplicated(keys)
        assert not dupes.any(), f"{name}: {dupes.sum()} duplicate rows on {keys}"

    country_sets = {
        "adm0": set(adm0["ID_0"]), "adm1": set(adm1["ID_0"]), "taxonomy": set(tax["ID_0"])
    }
    if not (country_sets["adm0"] == country_sets["adm1"] == country_sets["taxonomy"]):
        for a, b in (("adm0", "adm1"), ("adm0", "taxonomy")):
            diff = country_sets[a] ^ country_sets[b]
            if diff:
                print(f"  WARNING: country sets differ between {a} and {b}: {sorted(diff)}")

    n_adm1_units = adm1.groupby(["ID_0", "ID_1"], observed=True).ngroups
    assert n_adm1_units >= 3500, f"only {n_adm1_units} ADM1 units — checkout incomplete?"

    def spot(df: pd.DataFrame, filt: dict, expected: float, label: str) -> None:
        mask = pd.Series(True, index=df.index)
        for col, val in filt.items():
            mask &= df[col] == val
        got = df.loc[mask, config.UCC_COL]
        assert len(got) == 1, f"spot check {label}: {len(got)} rows matched {filt}"
        assert abs(got.iloc[0] - expected) <= 1.0, (
            f"spot check {label}: expected ~{expected}, got {got.iloc[0]}"
        )

    spot(adm0, {"ID_0": "VUT", "OCCUPANCY": "RES"}, 605, "Vanuatu RES ADM0")
    spot(adm1, {"ID_0": "VUT", "ID_1": "VU-MAP", "OCCUPANCY": "COM"}, 1458, "Malampa COM ADM1")

    # Recomputed UCC vs GEM's own column (rounded to ints in the source files).
    rels = []
    for df in (adm0, adm1, tax):
        src = pd.to_numeric(df[SOURCE_UCC], errors="coerce")
        mask = src.notna() & (src > 0) & (df["TOTAL_AREA_SQM"] > 0)
        recomputed = df.loc[mask, "BLDG_REPL_COST_USD"] / df.loc[mask, "TOTAL_AREA_SQM"]
        rels.append(((recomputed - src[mask]).abs() / src[mask]))
    rel = pd.concat(rels)
    assert rel.median() < 0.005, f"UCC recompute mismatch: median rel. diff {rel.median():.4f}"

    return {
        "countries": int(n_countries),
        "adm1_units": int(n_adm1_units),
        "adm0_rows": int(len(adm0)),
        "adm1_rows": int(len(adm1)),
        "taxonomy_rows": int(len(tax)),
    }


def cpi_adjustment() -> dict:
    """US CPI factor from GEM's (assumed) cost reference year to the latest
    complete year, via the World Bank API. Falls back to the cached series,
    then to no adjustment, so offline builds still succeed."""
    cache = config.CACHE_DIR / "wb_us_cpi.json"
    series = None
    try:
        body = requests.get(config.WB_CPI_API, timeout=60).json()
        series = {int(r["date"]): r["value"] for r in body[1] if r["value"] is not None}
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(series), encoding="utf-8")
    except Exception as err:
        print(f"  WARNING: WB CPI API unavailable ({err}); trying cache")
        if cache.exists():
            series = {int(k): v for k, v in json.loads(cache.read_text(encoding="utf-8")).items()}
    ref = config.GEM_COST_REF_YEAR
    if not series or ref not in series:
        print("  WARNING: no usable CPI series; UCCs left in GEM reference-year USD")
        return {"ref_year": ref, "target_year": ref, "factor": 1.0,
                "indicator": "FP.CPI.TOTL (USA)", "source": "api.worldbank.org"}
    target = max(series)
    factor = series[target] / series[ref]
    print(f"  CPI adjustment: {ref} -> {target} USD, factor {factor:.4f}")
    return {"ref_year": ref, "target_year": target, "factor": round(factor, 6),
            "indicator": "FP.CPI.TOTL (USA)", "source": "api.worldbank.org"}


def write_outputs(adm0: pd.DataFrame, adm1: pd.DataFrame, tax: pd.DataFrame,
                  gem_commit: str, counts: dict, adjustment: dict) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in (("ucc_adm0", adm0), ("ucc_adm1", adm1), ("ucc_taxonomy", tax)):
        df.drop(columns=[SOURCE_UCC]).to_csv(
            config.DATA_DIR / f"{name}.csv",
            index=False, encoding="utf-8", lineterminator="\n", float_format="%.1f",
        )

    meta_path = config.DATA_DIR / "source_metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    meta["generated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta["gem"] = {
        "repo": config.GEM_REPO_WEB,
        "commit": gem_commit,
        "license": config.GEM_LICENSE,
        "citation": config.GEM_CITATION,
    }
    meta["counts"] = counts
    meta["cost_adjustment"] = adjustment
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-fetch", action="store_true",
                        help="use the existing cache/gem checkout as-is")
    parser.add_argument("--gem-ref", default=None,
                        help="GEM commit/branch to build from (default: origin/main)")
    args = parser.parse_args()

    gem_commit = get_head() if args.skip_fetch else ensure_gem_checkout(args.gem_ref)
    print(f"GEM source commit: {gem_commit}")

    adjustment = cpi_adjustment()
    adm0 = finalize(add_total_rows(load_family("Adm0"), TOTAL_KEYS["Adm0"]), "Adm0", gem_commit)
    adm1 = finalize(add_total_rows(load_family("Adm1"), TOTAL_KEYS["Adm1"]), "Adm1", gem_commit)
    tax = finalize(aggregate_taxonomy(load_family("Taxonomy")), "Taxonomy", gem_commit)
    for df in (adm0, adm1, tax):
        df[config.UCC_ADJ_COL] = (df[config.UCC_COL] * adjustment["factor"]).round(1)

    counts = validate(adm0, adm1, tax)
    write_outputs(adm0, adm1, tax, gem_commit, counts, adjustment)
    print(f"OK: {counts}")


if __name__ == "__main__":
    main()
