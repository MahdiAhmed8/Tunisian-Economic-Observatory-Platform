# Data notes

This project keeps the full evidence trail used by the dashboard.

- `raw/` contains untouched World Bank API JSON responses, indicator metadata responses, archived INS pages, and the Ministry of Finance debt bulletin used for the latest snapshot.
- `processed/world_bank_indicators.csv` is the tidy historical panel used for the dashboard.
- `processed/tunisia_official_latest.csv` contains the latest national headline releases, their periods, notes, and direct source URLs.
- `processed/indicator_metadata.csv` preserves definitions and source organizations.
- `processed/dashboard_data.json` is the compact browser-ready dataset.
- `processed/refresh_manifest.json` records the extraction time and row counts.

Run `python scripts/fetch_data.py` to refresh all files. Values are not interpolated. Missing observations remain missing, and every card shows the year of its latest available observation.

## Sources

- World Bank Indicators API v2: https://api.worldbank.org/v2
- World Development Indicators methodology: https://datahelpdesk.worldbank.org/knowledgebase/articles/906531-methodologies
- Tunisia National Institute of Statistics (context and latest national releases): https://www.ins.tn/
- Tunisia Ministry of Finance (public-debt bulletin): https://www.finances.gov.tn/

World Bank indicators can combine national and international official sources; the exact source organization and definition for each series are stored in `indicator_metadata.csv`.
