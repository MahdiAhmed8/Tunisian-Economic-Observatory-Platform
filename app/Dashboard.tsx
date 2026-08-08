"use client";

import { useEffect, useMemo, useState } from "react";

type Row = {
  country_code: string;
  country: string;
  year: number;
  indicator_code: string;
  indicator: string;
  theme: string;
  unit: string;
  value: number;
  source: string;
};

type NationalRow = {
  indicator: string;
  value: number;
  unit: string;
  period: string;
  source: string;
  source_url: string;
  note: string;
};

type DashboardData = {
  generated_at: string;
  countries: Record<string, string>;
  indicators: Record<string, { label: string; unit: string; theme: string }>;
  world_bank: Row[];
  national_latest: NationalRow[];
};

const palette: Record<string, string> = {
  TUN: "#e94a35",
  DZA: "#16866b",
  MAR: "#bb7a1d",
  EGY: "#7c5cc4",
  JOR: "#3887b8",
  TUR: "#7d8790",
};

const focusIndicators = [
  "NY.GDP.MKTP.KD.ZG",
  "FP.CPI.TOTL.ZG",
  "SL.UEM.TOTL.ZS",
  "GC.DOD.TOTL.GD.ZS",
  "NE.TRD.GNFS.ZS",
  "BN.CAB.XOKA.GD.ZS",
  "SE.SEC.ENRR",
  "SE.TER.ENRR",
  "SE.XPD.TOTL.GD.ZS",
  "SH.XPD.CHEX.GD.ZS",
  "SP.DYN.LE00.IN",
  "SH.STA.MMRT",
];

const themes = ["All", "Growth", "Prices", "Jobs", "Public finance", "Trade", "Education", "Health"];

const timeline = [
  { year: 2011, title: "Transition year", text: "Output contracted sharply and unemployment rose. The chart lets you inspect the break in each series." },
  { year: 2020, title: "Pandemic shock", text: "GDP recorded its deepest contraction in the displayed period while trade and services were disrupted." },
  { year: 2023, title: "Inflation crest", text: "Annual inflation reached its recent high before easing in 2024 and 2025." },
  { year: 2026, title: "Latest national pulse", text: "INS reports 2.6% year-on-year growth in Q1, 15% unemployment in Q1, and 5.3% inflation in June." },
];

function fmt(value: number, unit: string, compact = false) {
  if (unit === "people" || unit.includes("million TND")) {
    return compact ? new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(value) : new Intl.NumberFormat("en").format(value);
  }
  return new Intl.NumberFormat("en", { maximumFractionDigits: 1, minimumFractionDigits: Math.abs(value) < 10 ? 1 : 0 }).format(value);
}

function ArrowIcon() {
  return <span aria-hidden="true">↗</span>;
}

function LineChart({ rows, countries, unit }: { rows: Row[]; countries: string[]; unit: string }) {
  const width = 900;
  const height = 330;
  const pad = { left: 54, right: 24, top: 24, bottom: 42 };
  const years = rows.map((row) => row.year);
  const values = rows.map((row) => row.value);
  const minYear = Math.min(...years);
  const maxYear = Math.max(...years);
  let minValue = Math.min(...values);
  let maxValue = Math.max(...values);
  const range = maxValue - minValue || 1;
  minValue -= range * 0.12;
  maxValue += range * 0.12;
  const x = (year: number) => pad.left + ((year - minYear) / Math.max(1, maxYear - minYear)) * (width - pad.left - pad.right);
  const y = (value: number) => pad.top + ((maxValue - value) / (maxValue - minValue)) * (height - pad.top - pad.bottom);
  const ticks = Array.from({ length: 5 }, (_, i) => minValue + ((maxValue - minValue) * i) / 4).reverse();
  const yearTicks = Array.from(new Set([minYear, Math.round(minYear + (maxYear - minYear) / 3), Math.round(minYear + ((maxYear - minYear) * 2) / 3), maxYear]));

  return (
    <div className="chart-wrap">
      <svg className="chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Historical chart, ${unit}`}>
        {ticks.map((tick) => (
          <g key={tick}>
            <line x1={pad.left} x2={width - pad.right} y1={y(tick)} y2={y(tick)} className="grid-line" />
            <text x={pad.left - 10} y={y(tick) + 4} textAnchor="end" className="axis-label">{fmt(tick, unit)}</text>
          </g>
        ))}
        {yearTicks.map((tick) => <text key={tick} x={x(tick)} y={height - 12} textAnchor="middle" className="axis-label">{tick}</text>)}
        {countries.map((code) => {
          const series = rows.filter((row) => row.country_code === code).sort((a, b) => a.year - b.year);
          const segments: Row[][] = [];
          series.forEach((point) => {
            const last = segments.at(-1)?.at(-1);
            if (!last || point.year - last.year > 2) segments.push([point]);
            else segments.at(-1)!.push(point);
          });
          return (
            <g key={code}>
              {segments.map((segment, index) => (
                <polyline key={index} points={segment.map((point) => `${x(point.year)},${y(point.value)}`).join(" ")} fill="none" stroke={palette[code]} strokeWidth={code === "TUN" ? 4 : 2.2} strokeLinecap="round" strokeLinejoin="round" opacity={code === "TUN" ? 1 : 0.8} />
              ))}
              {series.at(-1) && <circle cx={x(series.at(-1)!.year)} cy={y(series.at(-1)!.value)} r={code === "TUN" ? 5 : 3.5} fill={palette[code]} stroke="#fff" strokeWidth="2" />}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function explain(series: Row[]) {
  const sorted = [...series].sort((a, b) => a.year - b.year);
  const latest = sorted.at(-1);
  const previous = sorted.at(-2);
  if (!latest || !previous) return "There are not enough observations to describe a change.";
  const delta = latest.value - previous.value;
  const direction = Math.abs(delta) < 0.05 ? "was broadly unchanged" : delta > 0 ? "increased" : "decreased";
  const amount = Math.abs(delta);
  const pointWord = latest.unit.includes("year") ? "years" : "percentage points";
  return `${latest.indicator} ${direction}${Math.abs(delta) < 0.05 ? "" : ` by ${fmt(amount, latest.unit)} ${pointWord}`} between ${previous.year} and ${latest.year}. This describes the movement; it does not prove what caused it.`;
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [indicator, setIndicator] = useState("NY.GDP.MKTP.KD.ZG");
  const [theme, setTheme] = useState("All");
  const [countries, setCountries] = useState(["TUN", "DZA", "MAR"]);
  const [startYear, setStartYear] = useState(2000);
  const [endYear, setEndYear] = useState(2025);

  useEffect(() => {
    fetch("/data/dashboard_data.json").then((response) => response.json()).then(setData);
  }, []);

  const indicators = useMemo(() => {
    if (!data) return [];
    return focusIndicators.filter((code) => data.indicators[code] && (theme === "All" || data.indicators[code].theme === theme));
  }, [data, theme]);

  useEffect(() => {
    if (data && indicators.length && !indicators.includes(indicator)) setIndicator(indicators[0]);
  }, [data, indicators, indicator]);

  const rows = useMemo(() => data?.world_bank.filter((row) => row.indicator_code === indicator && row.year >= startYear && row.year <= endYear && countries.includes(row.country_code)) ?? [], [data, indicator, startYear, endYear, countries]);
  const tunisiaSeries = useMemo(() => rows.filter((row) => row.country_code === "TUN"), [rows]);

  if (!data) return <main className="loading"><span className="loader" />Loading the observatory…</main>;

  const national = Object.fromEntries(data.national_latest.map((row) => [row.indicator, row]));
  const tradeBalance = national["Merchandise exports"].value - national["Merchandise imports"].value;
  const education = data.world_bank.filter((row) => row.country_code === "TUN" && row.indicator_code === "SE.SEC.ENRR").sort((a, b) => b.year - a.year)[0];
  const health = data.world_bank.filter((row) => row.country_code === "TUN" && row.indicator_code === "SP.DYN.LE00.IN").sort((a, b) => b.year - a.year)[0];

  const headlineCards = [national["GDP growth"], national.Inflation, national.Unemployment, national["Public debt"]];
  const downloadReport = () => {
    const lines = [
      "# Tunisia economic snapshot",
      `Generated ${new Date(data.generated_at).toLocaleDateString("en-GB")}`,
      "",
      ...headlineCards.map((row) => `- ${row.indicator}: ${fmt(row.value, row.unit)} ${row.unit} (${row.period})`),
      `- Merchandise trade balance: ${fmt(tradeBalance, "million TND")} million TND (Jan–Jun 2026)`,
      "",
      "## Automatic reading",
      explain(tunisiaSeries),
      "",
      "Sources: World Bank WDI, Tunisia INS, Tunisia Ministry of Finance. See the project data folder for definitions and raw extracts.",
    ];
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([lines.join("\n")], { type: "text/markdown" }));
    link.download = "tunisia-economic-snapshot.md";
    link.click();
    URL.revokeObjectURL(link.href);
  };

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="Tunisian Economic Observatory home"><span className="brand-mark">TE</span><span>Tunisian Economic Observatory</span></a>
        <nav aria-label="Page navigation"><a href="#explore">Explore</a><a href="#timeline">Timeline</a><a href="#data">Data</a></nav>
        <button className="button secondary" onClick={downloadReport}>Download brief <span aria-hidden="true">↓</span></button>
      </header>

      <section className="hero" id="top">
        <div className="eyebrow"><span className="live-dot" /> Latest national pulse · 2026</div>
        <div className="hero-grid">
          <div>
            <h1>Tunisia’s economy,<br /><em>made legible.</em></h1>
            <p className="hero-copy">Explore three decades of growth, prices, jobs, public finances and human development—without the economic jargon.</p>
          </div>
          <div className="hero-note">
            <span>In one sentence</span>
            <p>Growth is positive and inflation has eased, but unemployment remains high and public debt leaves limited room for shocks.</p>
            <small>Latest releases from INS and the Ministry of Finance. Read as a snapshot, not a forecast.</small>
          </div>
        </div>
        <div className="headline-grid">
          {headlineCards.map((row) => (
            <a className="headline-card" href={row.source_url} target="_blank" rel="noreferrer" key={row.indicator}>
              <div><span>{row.indicator}</span><ArrowIcon /></div>
              <strong>{fmt(row.value, row.unit)}<small>{row.unit.startsWith("%") ? "%" : ""}</small></strong>
              <p>{row.period} · {row.source.includes("Statistics") ? "INS" : "Ministry of Finance"}</p>
            </a>
          ))}
        </div>
      </section>

      <section className="section explore" id="explore">
        <div className="section-heading">
          <div><span className="kicker">THE LONG VIEW</span><h2>What changed—and when?</h2></div>
          <p>Choose a measure, period and comparison group. Lines break where the source has missing years.</p>
        </div>

        <div className="theme-tabs" role="tablist" aria-label="Indicator themes">
          {themes.map((item) => <button key={item} role="tab" aria-selected={theme === item} onClick={() => setTheme(item)}>{item}</button>)}
        </div>

        <div className="chart-card">
          <div className="chart-controls">
            <label>Measure<select value={indicator} onChange={(event) => setIndicator(event.target.value)}>{indicators.map((code) => <option value={code} key={code}>{data.indicators[code].label}</option>)}</select></label>
            <div className="period-controls">
              <label>From<input type="number" min="1990" max={endYear} value={startYear} onChange={(event) => setStartYear(Number(event.target.value))} /></label>
              <label>To<input type="number" min={startYear} max="2025" value={endYear} onChange={(event) => setEndYear(Number(event.target.value))} /></label>
            </div>
          </div>
          <div className="country-chips" aria-label="Countries shown">
            {Object.entries(data.countries).map(([code, name]) => (
              <button key={code} className={countries.includes(code) ? "active" : ""} onClick={() => setCountries((current) => current.includes(code) ? (current.length === 1 ? current : current.filter((item) => item !== code)) : [...current, code])}>
                <span style={{ background: palette[code] }} />{name}
              </button>
            ))}
          </div>
          {rows.length ? <LineChart rows={rows} countries={countries} unit={data.indicators[indicator].unit} /> : <div className="no-data">No observations are available for this selection.</div>}
          <div className="chart-footer"><span>{data.indicators[indicator].unit}</span><span>Source: World Bank WDI · values last refreshed {new Date(data.generated_at).toLocaleDateString("en-GB")}</span></div>
        </div>

        <div className="insight-grid">
          <article className="insight primary"><span>AUTOMATIC READING</span><h3>{explain(tunisiaSeries)}</h3><p>Generated from the two latest available annual observations for Tunisia.</p></article>
          <article className="insight"><span>TRADE PULSE</span><h3>{fmt(tradeBalance, "million TND")}m TND</h3><p>Merchandise trade balance, Jan–Jun 2026. Exports were {fmt(national["Merchandise exports"].value, "million TND")}m; imports {fmt(national["Merchandise imports"].value, "million TND")}m.</p></article>
          <article className="insight"><span>PEOPLE</span><h3>{fmt(education.value, education.unit)}% enrolled</h3><p>Gross secondary enrollment in {education.year}. Life expectancy was {fmt(health.value, health.unit)} years in {health.year}.</p></article>
        </div>
      </section>

      <section className="section timeline-section" id="timeline">
        <div className="section-heading light"><div><span className="kicker">HISTORICAL TIMELINE</span><h2>Four moments that shape the chart</h2></div><p>Context labels help orient the reader. They are not claims of statistical causation.</p></div>
        <div className="timeline">
          {timeline.map((event, index) => <article key={event.year}><div className="year">{event.year}</div><div className="timeline-rule"><span>{String(index + 1).padStart(2, "0")}</span></div><h3>{event.title}</h3><p>{event.text}</p></article>)}
        </div>
      </section>

      <section className="section data-section" id="data">
        <div className="section-heading"><div><span className="kicker">OPEN DATA DESK</span><h2>Check the work. Reuse the data.</h2></div><p>Every chart traces back to a stored extract. No values are interpolated, and each figure keeps its observation period.</p></div>
        <div className="download-grid">
          <a href="/data/world_bank_indicators.csv" download><span>01</span><div><strong>Comparable annual panel</strong><p>2,990 rows · 16 indicators · 6 countries · CSV</p></div><b>↓</b></a>
          <a href="/data/tunisia_official_latest.csv" download><span>02</span><div><strong>Latest Tunisia releases</strong><p>INS + Ministry of Finance · CSV</p></div><b>↓</b></a>
          <a href="/data/dashboard_data.json" download><span>03</span><div><strong>Dashboard dataset</strong><p>Complete browser-ready bundle · JSON</p></div><b>↓</b></a>
          <button onClick={downloadReport}><span>04</span><div><strong>Plain-language brief</strong><p>Current selection and source note · Markdown</p></div><b>↓</b></button>
        </div>
        <div className="method-grid">
          <div><span>01</span><h3>Comparable history</h3><p>World Bank WDI annual series make cross-country comparisons possible. The exact definition and source organization are preserved in the project metadata.</p></div>
          <div><span>02</span><h3>National pulse</h3><p>INS provides the newest monthly and quarterly figures. These are shown separately because their frequency differs from the annual comparison series.</p></div>
          <div><span>03</span><h3>Debt caution</h3><p>The current debt card uses the Ministry of Finance’s broader public-debt measure. It should not be compared directly with the older WDI central-government series.</p></div>
        </div>
      </section>

      <footer><div className="brand"><span className="brand-mark">TE</span><span>Tunisian Economic Observatory</span></div><p>Public data, plain language, visible caveats.</p><div><a href="https://data.worldbank.org/country/tunisia" target="_blank" rel="noreferrer">World Bank <ArrowIcon /></a><a href="https://www.ins.tn/" target="_blank" rel="noreferrer">INS Tunisia <ArrowIcon /></a><a href="https://www.finances.gov.tn/" target="_blank" rel="noreferrer">Ministry of Finance <ArrowIcon /></a></div></footer>
    </main>
  );
}
