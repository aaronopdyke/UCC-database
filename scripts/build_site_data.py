"""Emit the static site's data files from the compiled UCC CSVs.

Outputs (docs/data/):
- ucc_adm0.csv / ucc_adm1.csv / ucc_taxonomy.csv  (download copies)
- countries/<ISO3>.json  (columnar per-country tables for the browse page)
- countries_index.json   (country picker)
- meta.json              (provenance + bins for footers/legend)
- refreshed UCC_* properties inside the committed boundary TopoJSONs, so a
  data-only refresh (no geometry rebuild) keeps the map in sync.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd

import config

COUNTRY_COLS = {
    "adm0": ["OCCUPANCY", "BUILDINGS", "TOTAL_AREA_SQM", "BLDG_REPL_COST_USD",
             config.UCC_COL, config.UCC_ADJ_COL, config.CONTENTS_COL],
    "adm1": ["ID_1", "NAME_1", "OCCUPANCY", "BUILDINGS", "TOTAL_AREA_SQM",
             "BLDG_REPL_COST_USD", config.UCC_COL, config.UCC_ADJ_COL, config.CONTENTS_COL],
    "taxonomy": ["OCCUPANCY", "MACRO_TAXONOMY", "TAXONOMY", "SETTLEMENT", "BUILDINGS",
                 "TOTAL_AREA_SQM", "BLDG_REPL_COST_USD", config.UCC_COL, config.UCC_ADJ_COL,
                 config.CONTENTS_COL],
}


def table_payload(df: pd.DataFrame, kind: str) -> dict:
    cols = COUNTRY_COLS[kind]
    sub = df[cols]
    return {"columns": cols, "rows": json.loads(sub.to_json(orient="values"))}


def write_country_files(adm0: pd.DataFrame, adm1: pd.DataFrame, tax: pd.DataFrame) -> list[dict]:
    config.COUNTRIES_DIR.mkdir(parents=True, exist_ok=True)
    index = []
    for iso, name, region in adm0[["ID_0", "NAME_0", "REGION"]].drop_duplicates().itertuples(index=False):
        c_adm0 = adm0[adm0["ID_0"] == iso]
        c_adm1 = adm1[adm1["ID_0"] == iso]
        c_tax = tax[tax["ID_0"] == iso]
        payload = {
            "iso3": iso,
            "name": name,
            "region": region,
            "gem_commit": c_adm0["GEM_COMMIT"].iloc[0],
            "adm0": table_payload(c_adm0, "adm0"),
            "adm1": table_payload(c_adm1, "adm1"),
            "taxonomy": table_payload(c_tax, "taxonomy"),
        }
        (config.COUNTRIES_DIR / f"{iso}.json").write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        total = c_adm0.loc[c_adm0["OCCUPANCY"] == "TOTAL", config.UCC_COL]
        index.append({
            "iso3": iso, "name": name, "region": region,
            "n_adm1": int(c_adm1["ID_1"].nunique()),
            "ucc_total": round(float(total.iloc[0])) if len(total) and pd.notna(total.iloc[0]) else None,
        })
    index.sort(key=lambda entry: entry["name"])

    # Drop stale country files (countries renamed/removed upstream).
    keep = {f"{entry['iso3']}.json" for entry in index}
    for path in config.COUNTRIES_DIR.glob("*.json"):
        if path.name not in keep:
            path.unlink()
    return index


def rebake_topojson(adm0: pd.DataFrame, adm1: pd.DataFrame,
                    cpi_factor: float = 1.0) -> None:
    """Refresh UCC_* properties inside the committed boundary TopoJSONs."""

    def ucc_props(frame: pd.DataFrame, keys: list[str]) -> dict:
        lookup: dict = {}
        for row in frame.itertuples(index=False):
            key = tuple(getattr(row, k) for k in keys)
            ucc = getattr(row, config.UCC_ADJ_COL, None)
            if ucc is None or pd.isna(ucc):
                ucc = getattr(row, config.UCC_COL)
            if pd.notna(ucc):
                lookup.setdefault(key, {})[f"UCC_{row.OCCUPANCY}"] = int(round(ucc))
        return lookup

    adm0_lookup = ucc_props(adm0, ["ID_0"])
    jobs = [
        ("boundaries_adm0.topojson", adm0_lookup,
         lambda p: (p.get("id"),), None),
        ("boundaries_adm1.topojson", ucc_props(adm1, ["ID_0", "ID_1"]),
         lambda p: (p.get("iso3"), p.get("gid")), adm1),
    ]
    for filename, lookup, key_of, frame in jobs:
        path = config.DOCS_DATA_DIR / filename
        if not path.exists():
            print(f"  {filename} not built yet; skipping rebake")
            continue
        topo = json.loads(path.read_text(encoding="utf-8"))
        for obj in topo.get("objects", {}).values():
            for geom in obj.get("geometries", []):
                props = geom.get("properties") or {}
                fresh = lookup.get(key_of(props))
                if fresh is None and props.get("natl"):
                    # National-average fallback polygon: refresh from ADM0.
                    fresh = adm0_lookup.get((props.get("iso3"),))
                if fresh is None and frame is not None and props.get("units"):
                    # Aggregated polygon: recompute area-weighted values over
                    # its member GEM units (kept self-describing via 'units').
                    members = props["units"].split(";")
                    sub = frame[(frame["ID_0"] == props.get("iso3"))
                                & (frame["ID_1"].isin(members))]
                    fresh = {}
                    for occ, grp in sub.groupby("OCCUPANCY", observed=True):
                        area = grp["TOTAL_AREA_SQM"].sum()
                        if area > 0:
                            fresh[f"UCC_{occ}"] = int(round(
                                grp["BLDG_REPL_COST_USD"].sum() / area * cpi_factor))
                if fresh is None and not any(k in props for k in ("gid", "id", "units", "natl")):
                    continue  # unmatched boundary unit: nothing to refresh
                for key in [k for k in props if k.startswith("UCC_")]:
                    del props[key]
                if fresh:
                    props.update(fresh)
        path.write_text(json.dumps(topo, ensure_ascii=False, separators=(",", ":")),
                        encoding="utf-8")
        print(f"  rebaked UCC values into {filename}")


def main() -> None:
    adm0 = pd.read_csv(config.DATA_DIR / "ucc_adm0.csv")
    adm1 = pd.read_csv(config.DATA_DIR / "ucc_adm1.csv")
    tax = pd.read_csv(config.DATA_DIR / "ucc_taxonomy.csv")

    config.DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("ucc_adm0.csv", "ucc_adm1.csv", "ucc_taxonomy.csv"):
        shutil.copyfile(config.DATA_DIR / name, config.DOCS_DATA_DIR / name)

    index = write_country_files(adm0, adm1, tax)
    (config.DOCS_DATA_DIR / "countries_index.json").write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )

    meta_path = config.DATA_DIR / "source_metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    adj = meta.get("cost_adjustment") or {}
    site_meta = {
        "generated_utc": meta.get("generated_utc"),
        "cost_year": adj.get("target_year"),
        "gem_cost_ref_year": adj.get("ref_year"),
        "cpi_factor": adj.get("factor"),
        "gem_commit": (meta.get("gem") or {}).get("commit"),
        "gem_repo": (meta.get("gem") or {}).get("repo"),
        "counts": meta.get("counts"),
        "wb": meta.get("world_bank_boundaries"),
        "bins": config.UCC_BINS,
        "occupancies": config.OCCUPANCY_ORDER,
    }
    (config.DOCS_DATA_DIR / "meta.json").write_text(
        json.dumps(site_meta, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    rebake_topojson(adm0, adm1, float(adj.get("factor") or 1.0))
    print(f"Site data written: {len(index)} countries")


if __name__ == "__main__":
    main()
