"""Tunisian Economic Observatory — Streamlit application.

Run with: streamlit run streamlit_app.py
"""

from __future__ import annotations

import html
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "processed"

COUNTRY_COLORS = {
    "Tunisia": "#e94a35",
    "Algeria": "#16866b",
    "Morocco": "#bb7a1d",
    "Egypt, Arab Rep.": "#7c5cc4",
    "Jordan": "#3887b8",
    "Turkiye": "#7d8790",
    "Türkiye": "#7d8790",
}

FOCUS_INDICATORS = [
    "GDP growth",
    "Inflation",
    "Unemployment",
    "Central government debt",
    "Exports",
    "Imports",
    "Trade openness",
    "Current account balance",
    "Secondary school enrollment",
    "Tertiary school enrollment",
    "Government education spending",
    "Current health spending",
    "Life expectancy",
    "Maternal mortality",
    "GDP per person",
]


st.set_page_config(
    page_title="Tunisian Economic Observatory",
    page_icon="🇹🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner=False)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    world_bank = pd.read_csv(DATA / "world_bank_indicators.csv")
    latest = pd.read_csv(DATA / "tunisia_official_latest.csv")
    metadata = pd.read_csv(DATA / "indicator_metadata.csv")
    manifest = pd.read_json(DATA / "refresh_manifest.json", typ="series").to_dict()
    world_bank["year"] = world_bank["year"].astype(int)
    return world_bank, latest, metadata, manifest


def latest_row(frame: pd.DataFrame, country: str, indicator: str) -> pd.Series | None:
    subset = frame[(frame["country"] == country) & (frame["indicator"] == indicator)].sort_values("year")
    return None if subset.empty else subset.iloc[-1]


def format_value(value: float, unit: str) -> str:
    if "people" in unit:
        return f"{value / 1_000_000:.1f}m"
    if "US$" in unit:
        return f"${value:,.0f}"
    if abs(value) >= 1_000:
        return f"{value:,.0f}"
    return f"{value:.1f}"


def automatic_explanation(frame: pd.DataFrame, indicator: str, country: str = "Tunisia") -> str:
    series = frame[(frame["country"] == country) & (frame["indicator"] == indicator)].sort_values("year")
    if len(series) < 2:
        return "There are not enough published observations to describe a recent change."
    latest, previous = series.iloc[-1], series.iloc[-2]
    change = float(latest["value"] - previous["value"])
    if abs(change) < 0.05:
        movement = "was broadly unchanged"
    else:
        direction = "increased" if change > 0 else "decreased"
        measure = "years" if latest["unit"] == "years" else "percentage points"
        movement = f"{direction} by {abs(change):.1f} {measure}"
    return (
        f"{indicator} {movement} between {int(previous['year'])} and {int(latest['year'])}. "
        "This describes the movement in the published series; it does not prove what caused it."
    )


def line_chart(frame: pd.DataFrame, indicator: str, countries: list[str], start: int, end: int) -> go.Figure:
    selected = frame[
        (frame["indicator"] == indicator)
        & frame["country"].isin(countries)
        & frame["year"].between(start, end)
    ].sort_values("year")
    unit = selected["unit"].iloc[0] if not selected.empty else ""
    figure = go.Figure()
    for country in countries:
        series = selected[selected["country"] == country]
        if series.empty:
            continue
        figure.add_trace(
            go.Scatter(
                x=series["year"],
                y=series["value"],
                name=country.replace(", Arab Rep.", ""),
                mode="lines",
                connectgaps=False,
                line={
                    "color": COUNTRY_COLORS.get(country, "#7d8790"),
                    "width": 4 if country == "Tunisia" else 2,
                },
                hovertemplate=f"<b>{html.escape(country)}</b><br>%{{x}}: %{{y:.2f}} {html.escape(unit)}<extra></extra>",
            )
        )
    figure.update_layout(
        height=430,
        margin={"l": 10, "r": 15, "t": 20, "b": 10},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.12, "x": 0},
        xaxis={"title": "", "showgrid": False, "dtick": 5},
        yaxis={"title": unit, "gridcolor": "#e7e4dc", "zerolinecolor": "#bbb8af"},
        font={"family": "Arial", "color": "#16201e"},
    )
    return figure


def ranking_chart(frame: pd.DataFrame, indicator: str, year: int) -> go.Figure:
    latest_by_country = []
    for country in frame["country"].unique():
        available = frame[
            (frame["country"] == country)
            & (frame["indicator"] == indicator)
            & (frame["year"] <= year)
        ].sort_values("year")
        if not available.empty:
            latest_by_country.append(available.iloc[-1])
    ranked = pd.DataFrame(latest_by_country).sort_values("value") if latest_by_country else pd.DataFrame()
    figure = go.Figure()
    if not ranked.empty:
        figure.add_trace(
            go.Bar(
                x=ranked["value"],
                y=ranked["country"].str.replace(", Arab Rep.", "", regex=False),
                orientation="h",
                marker_color=[COUNTRY_COLORS.get(country, "#7d8790") for country in ranked["country"]],
                text=[f"{value:.1f} · {int(obs_year)}" for value, obs_year in zip(ranked["value"], ranked["year"])],
                textposition="outside",
                hovertemplate="%{y}: %{x:.2f}<extra></extra>",
            )
        )
    figure.update_layout(
        height=420,
        margin={"l": 10, "r": 70, "t": 20, "b": 20},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        xaxis={"showgrid": True, "gridcolor": "#e7e4dc", "title": "Latest value available by selected year"},
        yaxis={"title": ""},
        font={"family": "Arial", "color": "#16201e"},
    )
    return figure


def build_report(latest: pd.DataFrame, wb: pd.DataFrame, indicator: str) -> str:
    records = {row["indicator"]: row for _, row in latest.iterrows()}
    exports = records["Merchandise exports"]["value"]
    imports = records["Merchandise imports"]["value"]
    lines = [
        "# Tunisia economic snapshot",
        "",
        "## Latest official pulse",
    ]
    for label in ["GDP growth", "Inflation", "Unemployment", "Public debt"]:
        row = records[label]
        lines.append(f"- **{label}:** {row['value']:.1f} {row['unit']} ({row['period']})")
    lines.extend(
        [
            f"- **Merchandise trade balance:** {exports - imports:,.1f} million TND (Jan–Jun 2026)",
            "",
            "## Automatic reading",
            automatic_explanation(wb, indicator),
            "",
            "## Sources",
            "World Bank World Development Indicators; Tunisia National Institute of Statistics; Tunisia Ministry of Finance.",
            "",
            "National headline figures and annual international series can use different definitions and frequencies. They are kept separate in the dashboard.",
        ]
    )
    return "\n".join(lines)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;1,400&family=DM+Sans:wght@400;500;600;700&display=swap');
        :root { --ink:#16201e; --muted:#68716f; --cream:#fbfaf5; --paper:#f3f0e8; --red:#e94a35; --green:#163f37; --lime:#cedb82; }
        .stApp { background: var(--cream); color: var(--ink); font-family:'DM Sans',sans-serif; }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] { background:#111816; }
        [data-testid="stSidebar"] * { color:#e9efed; }
        [data-testid="stSidebar"] hr { border-color:#34423f; }
        [data-testid="stSidebar"] .stSelectbox label, [data-testid="stSidebar"] .stMultiSelect label, [data-testid="stSidebar"] .stSlider label { color:#b8c4c1; }
        [data-testid="stSidebar"] [data-baseweb="select"] * { color:#16201e; }
        .block-container { max-width:1320px; padding-top:2.2rem; padding-bottom:4rem; }
        h1, h2, h3 { font-family:'Libre Baskerville',serif !important; letter-spacing:-.035em; }
        h1 { font-size:clamp(3rem,7vw,6.8rem) !important; line-height:.96 !important; font-weight:400 !important; margin-bottom:1.3rem !important; }
        h2 { font-size:clamp(2rem,4vw,3.8rem) !important; font-weight:400 !important; }
        .hero-kicker { color:var(--red); font-size:.72rem; letter-spacing:.16em; font-weight:700; margin-bottom:1rem; }
        .hero-sub { color:#58635f; font-size:1.12rem; line-height:1.65; max-width:760px; margin-bottom:2rem; }
        .plain-note { background:var(--green); color:white; padding:1.4rem 1.5rem; border-radius:14px; border-left:5px solid var(--lime); margin:1rem 0 2rem; }
        .plain-note span { color:var(--lime); font-size:.68rem; letter-spacing:.15em; font-weight:700; }
        .plain-note p { font-family:'Libre Baskerville',serif; font-size:1.15rem; line-height:1.55; margin:.7rem 0 0; }
        [data-testid="stMetric"] { background:#fff; border:1px solid #dedbd2; padding:1rem 1.1rem; border-radius:13px; min-height:135px; }
        [data-testid="stMetricLabel"] { color:#68716f; }
        [data-testid="stMetricValue"] { font-family:'Libre Baskerville',serif; }
        .auto-reading { background:var(--red); color:white; padding:1.4rem 1.5rem; border-radius:14px; margin:1rem 0; }
        .auto-reading b { display:block; color:#ffe4df; font-size:.68rem; letter-spacing:.14em; margin-bottom:.65rem; }
        .auto-reading p { font-family:'Libre Baskerville',serif; font-size:1.16rem; line-height:1.5; margin:0; }
        .context-card { background:#fff; border:1px solid #dedbd2; border-radius:12px; padding:1.1rem; min-height:205px; }
        .context-card strong { color:var(--red); font-family:'Libre Baskerville',serif; font-size:1.7rem; }
        .context-card h4 { margin:.75rem 0 .45rem; }
        .context-card p { color:#68716f; font-size:.86rem; line-height:1.55; }
        .source-note { color:#7a817f; font-size:.78rem; border-top:1px solid #dedbd2; padding-top:.8rem; }
        .stTabs [data-baseweb="tab-list"] { gap:1.1rem; border-bottom:1px solid #d8d5cc; }
        .stTabs [data-baseweb="tab"] { height:3.2rem; }
        .stTabs [aria-selected="true"] { color:var(--red) !important; }
        .stDownloadButton button { border-radius:999px; border:1px solid var(--green); }
        .stDownloadButton button:hover { background:var(--green); color:white; }
        div[data-testid="stDataFrame"] { border:1px solid #dedbd2; border-radius:10px; overflow:hidden; }
        @media (max-width:700px) { .block-container { padding-left:1rem; padding-right:1rem; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


wb, official, metadata, manifest = load_data()
inject_styles()

with st.sidebar:
    st.markdown("### 🇹🇳 Economic Observatory")
    st.caption("Public data · plain language")
    st.divider()
    theme = st.selectbox("Theme", ["All"] + sorted(wb["theme"].dropna().unique().tolist()))
    available_indicators = [
        item for item in FOCUS_INDICATORS
        if item in wb["indicator"].unique() and (theme == "All" or wb.loc[wb["indicator"] == item, "theme"].iloc[0] == theme)
    ]
    selected_indicator = st.selectbox("Indicator", available_indicators)
    country_options = wb["country"].drop_duplicates().tolist()
    selected_countries = st.multiselect(
        "Compare countries",
        country_options,
        default=[country for country in ["Tunisia", "Algeria", "Morocco"] if country in country_options],
    )
    selected_countries = selected_countries or ["Tunisia"]
    year_range = st.slider("Years", 1990, 2025, (2000, 2025))
    st.divider()
    st.caption(f"Refreshed {str(manifest['generated_at'])[:10]} · {int(manifest['world_bank_rows']):,} comparable observations")
    st.download_button(
        "Download current brief",
        build_report(official, wb, selected_indicator),
        file_name="tunisia_economic_snapshot.md",
        mime="text/markdown",
        width="stretch",
    )

st.markdown('<div class="hero-kicker">TUNISIAN ECONOMIC OBSERVATORY · 2026</div>', unsafe_allow_html=True)
st.markdown("# Tunisia’s economy, *made legible.*")
st.markdown(
    '<p class="hero-sub">Explore three decades of growth, prices, jobs, debt, trade and human development with checkable public data—and without the economic jargon.</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="plain-note"><span>IN ONE SENTENCE</span><p>Growth is positive and inflation has eased, but unemployment remains high and public debt leaves limited room for shocks.</p></div>',
    unsafe_allow_html=True,
)

official_map = {row["indicator"]: row for _, row in official.iterrows()}
metric_columns = st.columns(4)
for column, label in zip(metric_columns, ["GDP growth", "Inflation", "Unemployment", "Public debt"]):
    row = official_map[label]
    with column:
        st.metric(label, f"{row['value']:.1f}%", row["period"], delta_color="off")
        st.caption("INS Tunisia" if "Statistics" in row["source"] else "Ministry of Finance")

overview_tab, compare_tab, timeline_tab, data_tab, methods_tab = st.tabs(
    ["Long view", "Compare", "Timeline", "Downloads", "Sources & methods"]
)

with overview_tab:
    st.markdown("## What changed—and when?")
    st.caption("Select the measure, countries and years in the sidebar. Missing observations are not interpolated.")
    st.plotly_chart(
        line_chart(wb, selected_indicator, selected_countries, year_range[0], year_range[1]),
        width="stretch",
        config={"displaylogo": False, "toImageButtonOptions": {"filename": f"tunisia_{selected_indicator.lower().replace(' ', '_')}"}},
    )
    st.markdown(
        f'<div class="auto-reading"><b>AUTOMATIC READING</b><p>{html.escape(automatic_explanation(wb, selected_indicator))}</p></div>',
        unsafe_allow_html=True,
    )
    left, middle, right = st.columns(3)
    exports = official_map["Merchandise exports"]["value"]
    imports = official_map["Merchandise imports"]["value"]
    education = latest_row(wb, "Tunisia", "Secondary school enrollment")
    health = latest_row(wb, "Tunisia", "Life expectancy")
    with left:
        st.markdown("### Trade pulse")
        st.metric("Merchandise balance", f"{exports - imports:,.0f}m TND", "Jan–Jun 2026", delta_color="off")
        st.caption(f"Exports {exports:,.0f}m · Imports {imports:,.0f}m TND")
    with middle:
        st.markdown("### Education")
        if education is not None:
            st.metric("Secondary enrollment", f"{education['value']:.1f}%", str(int(education["year"])), delta_color="off")
        st.caption("Gross enrollment can exceed 100% because it counts students outside the official age range.")
    with right:
        st.markdown("### Health")
        if health is not None:
            st.metric("Life expectancy", f"{health['value']:.1f} years", str(int(health["year"])), delta_color="off")
        st.caption("Latest World Bank annual observation available in the extract.")

with compare_tab:
    st.markdown("## Tunisia versus peers")
    st.caption("Each bar uses the latest published observation on or before the chosen end year; the observation year is printed next to its value.")
    st.plotly_chart(ranking_chart(wb, selected_indicator, year_range[1]), width="stretch", config={"displaylogo": False})
    comparison = []
    for country in selected_countries:
        row = latest_row(wb[wb["year"] <= year_range[1]], country, selected_indicator)
        if row is not None:
            comparison.append({"Country": country, "Value": row["value"], "Unit": row["unit"], "Year": int(row["year"])})
    st.dataframe(pd.DataFrame(comparison), hide_index=True, width="stretch")

with timeline_tab:
    st.markdown("## Four moments that shape the chart")
    st.caption("These labels provide context; they are not claims of statistical causation.")
    events = [
        (2011, "Transition year", "Output contracted sharply and unemployment rose. Use the long-view chart to inspect the break in each series."),
        (2020, "Pandemic shock", "GDP recorded its deepest contraction in the displayed period while trade and services were disrupted."),
        (2023, "Inflation crest", "Annual inflation reached its recent high before easing in 2024 and 2025."),
        (2026, "Latest national pulse", "INS reports 2.6% year-on-year growth in Q1, 15% unemployment in Q1, and 5.3% inflation in June."),
    ]
    columns = st.columns(4)
    for column, (year, title, text) in zip(columns, events):
        with column:
            st.markdown(f'<div class="context-card"><strong>{year}</strong><h4>{title}</h4><p>{text}</p></div>', unsafe_allow_html=True)

with data_tab:
    st.markdown("## Check the work. Reuse the data.")
    st.caption("The project preserves raw responses, tidy tables, definitions and source links.")
    filtered = wb[
        (wb["indicator"] == selected_indicator)
        & wb["country"].isin(selected_countries)
        & wb["year"].between(year_range[0], year_range[1])
    ].sort_values(["country", "year"])
    first, second, third = st.columns(3)
    with first:
        st.download_button("Download current selection", filtered.to_csv(index=False), "current_selection.csv", "text/csv", width="stretch")
    with second:
        st.download_button("Download full World Bank panel", wb.to_csv(index=False), "world_bank_indicators.csv", "text/csv", width="stretch")
    with third:
        st.download_button("Download latest Tunisia releases", official.to_csv(index=False), "tunisia_official_latest.csv", "text/csv", width="stretch")
    st.dataframe(filtered, hide_index=True, width="stretch", height=430)

with methods_tab:
    st.markdown("## Sources and measurement boundaries")
    st.markdown(
        """
        **World Bank WDI** supplies the comparable annual panel. Its indicator definitions and source organizations are stored in `data/processed/indicator_metadata.csv`.

        **Tunisia’s National Institute of Statistics (INS)** supplies the newest monthly and quarterly growth, inflation, unemployment and merchandise-trade headlines.

        **Tunisia’s Ministry of Finance** supplies the end-2025 public-debt headline. It is broader than the older World Bank central-government debt series, so the two are displayed separately.

        No observations are interpolated. Every headline states its period, and chart lines break across longer data gaps.
        """
    )
    st.markdown('<p class="source-note">Automatic explanations compare the two latest available annual observations. They describe direction and size only; they do not assign causes or provide forecasts.</p>', unsafe_allow_html=True)
    with st.expander("Indicator catalogue"):
        st.dataframe(metadata[["code", "label", "theme", "unit", "source_name", "source_organization"]], hide_index=True, width="stretch")
