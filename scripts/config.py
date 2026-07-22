"""Shared configuration for the UCC-database build pipeline."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# --- Local directories -------------------------------------------------------
CACHE_DIR = REPO_ROOT / "cache"          # gitignored
GEM_CACHE = CACHE_DIR / "gem"            # sparse checkout of the GEM repo
WB_CACHE = CACHE_DIR / "wb"              # World Bank boundary downloads
DATA_DIR = REPO_ROOT / "data"            # canonical committed outputs
DOCS_DIR = REPO_ROOT / "docs"            # GitHub Pages root
DOCS_DATA_DIR = DOCS_DIR / "data"
COUNTRIES_DIR = DOCS_DATA_DIR / "countries"

# --- GEM global exposure model source ---------------------------------------
GEM_REPO_URL = "https://github.com/gem/global_exposure_model.git"
GEM_REPO_WEB = "https://github.com/gem/global_exposure_model"
GEM_LICENSE = "CC BY-NC-SA 4.0"
GEM_CITATION = (
    "Yepes-Estrada, C., Calderon, A., Costa, C., Crowley, H., Dabbeek, J., "
    "Hoyos, M.C., Martins, L., Paul, N., Rao, A., Silva, V. (2023). "
    "Global Building Exposure Model for Earthquake Risk Assessment. "
    "Earthquake Spectra, 39(4). https://doi.org/10.1177/87552930231194048"
)

# Only these three per-country summary families are needed; the leading
# "/*/*/" anchors to <Region>/<Country>/ and so excludes World/summaries.
GEM_SPARSE_PATTERNS = [
    "/*/*/summaries/Exposure_Summary_Adm0.csv",
    "/*/*/summaries/Exposure_Summary_Adm1.csv",
    "/*/*/summaries/Exposure_Summary_Taxonomy.csv",
]

# --- World Bank Official Boundaries source -----------------------------------
WB_DATASET_ID = "0038272"
WB_DATASET_WEB = (
    "https://datacatalog.worldbank.org/search/dataset/0038272/World-Bank-Official-Boundaries"
)
# The catalog's metadata API (datacatalogapi.worldbank.org) aggressively
# rate-limits anonymous clients, but the dataset publishes a stable manifest
# CSV (file_name,download_link) on the un-throttled file host. That manifest
# is the machine-readable entry point we build from.
WB_GEOJSON_MANIFEST_URL = (
    "https://datacatalogfiles.worldbank.org/ddh-published/0038272/2/DR0095369/DR0095369.csv"
)
WB_ADM1_ADDCOLS_URL = (
    "https://datacatalogfiles.worldbank.org/ddh-published/0038272/DR0095373/"
    "WB_Official_Boundaries_Admin1_additional_columns.csv"
)
WB_LICENSE = "CC BY 4.0"
WB_ATTRIBUTION = "World Bank Official Boundaries (World Bank Data Catalog)"

# --- Cost adjustment ----------------------------------------------------------
# GEM v2026.0.0 does not pin a single global cost reference year in its
# documentation; 2024 is assumed (major-release cadence; user-confirmed
# belief). Change here if GEM documents a different vintage.
GEM_COST_REF_YEAR = 2024
# World Bank US CPI (FP.CPI.TOTL) used to express UCCs in current USD.
WB_CPI_API = (
    "https://api.worldbank.org/v2/country/USA/indicator/FP.CPI.TOTL"
    "?format=json&per_page=100"
)

# --- Output conventions -------------------------------------------------------
# NONRES appears only where a country's non-residential stock is not split
# into COM/IND (currently New Zealand alone).
OCCUPANCY_ORDER = ["RES", "COM", "IND", "NONRES", "TOTAL"]
MEASURES = ["BUILDINGS", "TOTAL_AREA_SQM", "BLDG_REPL_COST_USD", "COST_CONTENTS_USD"]
UCC_COL = "UCC_USD_PER_SQM"
UCC_ADJ_COL = "UCC_ADJ_USD_PER_SQM"
# GEM contents replacement cost per m2 (separate from UCC, which is building-only)
CONTENTS_COL = "CONTENTS_USD_PER_SQM"

# Fixed choropleth class breaks (USD/m2), shared by the map and legend.
UCC_BINS = [100, 200, 400, 800, 1600, 3200]

# Hard size budgets for the web boundary files (bytes).
ADM0_TOPOJSON_BUDGET = 1_500_000
ADM1_TOPOJSON_BUDGET = 10_000_000
