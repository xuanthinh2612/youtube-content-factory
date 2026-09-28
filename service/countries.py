"""Country and territory names used by the project audience selector."""

import json
from pathlib import Path


DATA_DIRECTORY = Path(__file__).resolve().parent / "data"
COUNTRY_NAMES_EN_BY_CODE = json.loads((DATA_DIRECTORY / "countries.json").read_text(encoding="utf-8"))
COUNTRY_NAMES_VI_BY_CODE = json.loads((DATA_DIRECTORY / "countries_vi.json").read_text(encoding="utf-8"))
# Primary country languages derived from CLDR territory language populations.
COUNTRY_OUTPUT_LANGUAGE_BY_CODE = json.loads((DATA_DIRECTORY / "country_output_languages.json").read_text(encoding="utf-8"))

# Ranked by YouTube advertising audience in January 2025 (DataReportal/Kepios).
TOP_YOUTUBE_COUNTRY_CODES = (
    "IN", "US", "BR", "ID", "MX", "JP", "DE", "VN", "PH", "TR",
    "PK", "GB", "EG", "FR", "TH", "BD", "KR", "IT", "ES", "AR",
)

COUNTRY_OPTIONS = tuple(
    (code, COUNTRY_NAMES_VI_BY_CODE.get(code, COUNTRY_NAMES_EN_BY_CODE[code]))
    for code in sorted(
        COUNTRY_NAMES_EN_BY_CODE,
        key=lambda item: COUNTRY_NAMES_VI_BY_CODE.get(item, COUNTRY_NAMES_EN_BY_CODE[item]).casefold(),
    )
    if code != "AQ"
)
TOP_COUNTRY_OPTIONS = tuple(
    (code, COUNTRY_NAMES_VI_BY_CODE.get(code, COUNTRY_NAMES_EN_BY_CODE[code]))
    for code in TOP_YOUTUBE_COUNTRY_CODES
)
OTHER_COUNTRY_OPTIONS = tuple(item for item in COUNTRY_OPTIONS if item[0] not in TOP_YOUTUBE_COUNTRY_CODES)
VALID_COUNTRY_CODES = frozenset(code for code, _ in COUNTRY_OPTIONS)


