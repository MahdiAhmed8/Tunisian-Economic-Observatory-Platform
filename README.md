# Tunisian Economic Observatory

An interactive, plain-language dashboard for exploring Tunisia's economic evolution and comparing it with Algeria, Morocco, Egypt, Jordan, and Türkiye.

## What is included

- Historical GDP growth, inflation, unemployment, debt, trade, education, and health indicators
- Latest official Tunisia snapshot from INS and the Ministry of Finance
- Country comparison controls and a historical context timeline
- Automatic descriptions of the latest changes
- Downloadable CSV, JSON, and Markdown snapshot report
- A reproducible Python/Pandas data refresh pipeline with raw responses, processed tables, definitions, and source URLs

## Refresh the data

```powershell
python scripts/fetch_data.py
```

The refresh script writes untouched World Bank responses to `data/raw`, tidy tables to `data/processed`, and browser-ready exports to `public/data`. See `data/README.md` for the full provenance notes.

## Run locally

```powershell
npm install
npm run dev
```

The interface is built with React/vinext and native SVG charts. Python and Pandas handle the data preparation; the World Bank API is the main comparable-data source.

## Source boundaries

- World Bank WDI annual series support like-for-like historical comparisons.
- Tunisia INS releases supply newer monthly and quarterly headlines.
- The Ministry of Finance supplies the latest public-debt headline.
- National and international series can use different definitions. The dashboard keeps them visibly separate and does not interpolate missing observations.
