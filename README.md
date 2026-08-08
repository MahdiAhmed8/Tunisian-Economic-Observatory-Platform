# Tunisian Economic Observatory

An interactive dashboard built with the requested stack: **Python, Pandas, Plotly, and Streamlit**.

## Run the dashboard

```powershell
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Streamlit will print a local URL, normally `http://localhost:8501`.

## Refresh the source data

```powershell
python scripts/fetch_data.py
```

The refresh pipeline uses Pandas to transform World Bank API responses into tidy CSV and JSON files. It writes:

- Untouched responses and archived official releases to `data/raw`
- Analysis-ready tables to `data/processed`
- Browser-ready exports to `public/data`

See `data/README.md` for provenance, definitions, and measurement cautions.

## Dashboard capabilities

- GDP growth, inflation, unemployment, public debt, trade, education, and health
- Historical comparisons with Algeria, Morocco, Egypt, Jordan, and Türkiye
- Interactive Plotly time-series and ranking charts
- Plain-language automatic explanations
- Historical context timeline
- Downloadable selections, full datasets, and Markdown reports
- Separate treatment of comparable annual series and newer Tunisian national releases

The earlier React/Sites prototype remains in `app/` only as a preserved prototype. `streamlit_app.py` is the primary requested implementation.
