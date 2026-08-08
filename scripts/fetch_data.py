"""Fetch and prepare the Tunisian Economic Observatory datasets.

Sources:
- World Bank Indicators API v2 (annual observations and indicator metadata)
- IMF World Economic Outlook, April 2026 (official Excel bulk download)

The script deliberately keeps raw responses alongside tidy CSV/JSON outputs so
the provenance and transformations are inspectable.
"""

from __future__ import annotations

import json
import math
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PUBLIC = ROOT / "public" / "data"

COUNTRIES = {
    "TUN": "Tunisia",
    "DZA": "Algeria",
    "MAR": "Morocco",
    "EGY": "Egypt",
    "JOR": "Jordan",
    "TUR": "Türkiye",
}

INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": {"label": "GDP growth", "unit": "%", "theme": "Growth"},
    "NY.GDP.PCAP.KD": {"label": "GDP per person", "unit": "constant 2015 US$", "theme": "Growth"},
    "FP.CPI.TOTL.ZG": {"label": "Inflation", "unit": "%", "theme": "Prices"},
    "SL.UEM.TOTL.ZS": {"label": "Unemployment", "unit": "% of labor force", "theme": "Jobs"},
    "GC.DOD.TOTL.GD.ZS": {"label": "Central government debt", "unit": "% of GDP", "theme": "Public finance"},
    "NE.EXP.GNFS.ZS": {"label": "Exports", "unit": "% of GDP", "theme": "Trade"},
    "NE.IMP.GNFS.ZS": {"label": "Imports", "unit": "% of GDP", "theme": "Trade"},
    "NE.TRD.GNFS.ZS": {"label": "Trade openness", "unit": "% of GDP", "theme": "Trade"},
    "BN.CAB.XOKA.GD.ZS": {"label": "Current account balance", "unit": "% of GDP", "theme": "Trade"},
    "SE.SEC.ENRR": {"label": "Secondary school enrollment", "unit": "% gross", "theme": "Education"},
    "SE.TER.ENRR": {"label": "Tertiary school enrollment", "unit": "% gross", "theme": "Education"},
    "SE.XPD.TOTL.GD.ZS": {"label": "Government education spending", "unit": "% of GDP", "theme": "Education"},
    "SH.XPD.CHEX.GD.ZS": {"label": "Current health spending", "unit": "% of GDP", "theme": "Health"},
    "SP.DYN.LE00.IN": {"label": "Life expectancy", "unit": "years", "theme": "Health"},
    "SH.STA.MMRT": {"label": "Maternal mortality", "unit": "per 100,000 live births", "theme": "Health"},
    "SP.POP.TOTL": {"label": "Population", "unit": "people", "theme": "People"},
}

WB_BASE = "https://api.worldbank.org/v2"
NATIONAL_LATEST = [
    {
        "indicator": "GDP growth",
        "value": 2.6,
        "unit": "% year-on-year",
        "period": "2026 Q1",
        "source": "Tunisia National Institute of Statistics (INS)",
        "source_url": "https://www.ins.tn/en/publication/gross-domestic-product-gdp-first-quarter-2026",
        "note": "Seasonally adjusted real GDP; preliminary quarterly national accounts.",
    },
    {
        "indicator": "Inflation",
        "value": 5.3,
        "unit": "% year-on-year",
        "period": "June 2026",
        "source": "Tunisia National Institute of Statistics (INS)",
        "source_url": "https://www.ins.tn/publication/indice-des-prix-la-consommation-juin-2026",
        "note": "Consumer price inflation; monthly national release.",
    },
    {
        "indicator": "Unemployment",
        "value": 15.0,
        "unit": "% of labor force",
        "period": "2026 Q1",
        "source": "Tunisia National Institute of Statistics (INS)",
        "source_url": "https://www.ins.tn/publication/indicateurs-de-lemploi-et-du-chomage-premier-trimestre-2026",
        "note": "Quarterly labor force release.",
    },
    {
        "indicator": "Public debt",
        "value": 82.4,
        "unit": "% of GDP",
        "period": "End-2025",
        "source": "Tunisia Ministry of Finance",
        "source_url": "https://www.finances.gov.tn/sites/default/files/2026-02/R%C3%A9sultats%20provisoires%20de%20l%27ex%C3%A9cution%20du%20Budget%20%C3%A0%20fin%20D%C3%A9cembre%202025.pdf",
        "note": "Provisional budget execution; outstanding public debt.",
    },
    {
        "indicator": "Merchandise exports",
        "value": 34645.2,
        "unit": "million TND, year-to-date",
        "period": "Jan–Jun 2026",
        "source": "Tunisia National Institute of Statistics (INS)",
        "source_url": "https://www.ins.tn/",
        "note": "Current-price merchandise trade, first six months of 2026.",
    },
    {
        "indicator": "Merchandise imports",
        "value": 47214.6,
        "unit": "million TND, year-to-date",
        "period": "Jan–Jun 2026",
        "source": "Tunisia National Institute of Statistics (INS)",
        "source_url": "https://www.ins.tn/",
        "note": "Current-price merchandise trade, first six months of 2026.",
    },
]


def fetch_json(url: str) -> object:
    request = urllib.request.Request(url, headers={"User-Agent": "Tunisian-Economic-Observatory/1.0"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.load(response)
        except (urllib.error.HTTPError, urllib.error.URLError):
            if attempt == 4:
                raise
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Unable to fetch {url}")


def clean_number(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return round(float(value), 4)


def fetch_world_bank() -> tuple[pd.DataFrame, list[dict]]:
    rows: list[dict] = []
    metadata: list[dict] = []
    country_codes = ";".join(COUNTRIES)

    for code, config in INDICATORS.items():
        print(f"World Bank: {code}", flush=True)
        data_url = (
            f"{WB_BASE}/country/{country_codes}/indicator/{code}"
            "?format=json&date=1990:2025&per_page=20000"
        )
        payload = fetch_json(data_url)
        (RAW / f"wb_{code}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if isinstance(payload, list) and len(payload) > 1 and payload[1]:
            for item in payload[1]:
                if item.get("value") is None:
                    continue
                rows.append(
                    {
                        "country_code": item["countryiso3code"],
                        "country": item["country"]["value"],
                        "year": int(item["date"]),
                        "indicator_code": code,
                        "indicator": config["label"],
                        "theme": config["theme"],
                        "unit": config["unit"],
                        "value": clean_number(item["value"]),
                        "source": "World Bank WDI",
                    }
                )

        meta_url = f"{WB_BASE}/indicator/{code}?format=json"
        meta_payload = fetch_json(meta_url)
        (RAW / f"wb_metadata_{code}.json").write_text(
            json.dumps(meta_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        meta = meta_payload[1][0] if isinstance(meta_payload, list) and len(meta_payload) > 1 else {}
        metadata.append(
            {
                "code": code,
                "label": config["label"],
                "theme": config["theme"],
                "unit": config["unit"],
                "source_name": meta.get("source", {}).get("value", "World Development Indicators"),
                "source_note": meta.get("sourceNote", ""),
                "source_organization": meta.get("sourceOrganization", ""),
                "api_url": data_url,
            }
        )

    frame = pd.DataFrame(rows).sort_values(["indicator_code", "country_code", "year"])
    return frame, metadata


def build_snapshot(frame: pd.DataFrame) -> list[dict]:
    snapshot = []
    for code in [
        "NY.GDP.MKTP.KD.ZG",
        "FP.CPI.TOTL.ZG",
        "SL.UEM.TOTL.ZS",
        "GC.DOD.TOTL.GD.ZS",
        "NE.TRD.GNFS.ZS",
        "SP.DYN.LE00.IN",
    ]:
        subset = frame[(frame.country_code == "TUN") & (frame.indicator_code == code)].sort_values("year")
        if subset.empty:
            continue
        current = subset.iloc[-1]
        previous = subset.iloc[-2] if len(subset) > 1 else current
        snapshot.append(
            {
                "code": code,
                "label": current.indicator,
                "unit": current.unit,
                "value": clean_number(current.value),
                "year": int(current.year),
                "change": clean_number(current.value - previous.value),
                "previous_year": int(previous.year),
            }
        )
    return snapshot


def main() -> None:
    for directory in (RAW, PROCESSED, PUBLIC):
        directory.mkdir(parents=True, exist_ok=True)

    wb, metadata = fetch_world_bank()
    national = pd.DataFrame(NATIONAL_LATEST)
    wb.to_csv(PROCESSED / "world_bank_indicators.csv", index=False)
    national.to_csv(PROCESSED / "tunisia_official_latest.csv", index=False)
    pd.DataFrame(metadata).to_csv(PROCESSED / "indicator_metadata.csv", index=False)

    generated_at = datetime.now(timezone.utc).isoformat()
    dashboard = {
        "generated_at": generated_at,
        "countries": COUNTRIES,
        "indicators": INDICATORS,
        "snapshot": build_snapshot(wb),
        "world_bank": wb.to_dict(orient="records"),
        "national_latest": national.to_dict(orient="records"),
        "sources": {
            "world_bank": "https://api.worldbank.org/v2",
            "ins_tunisia": "https://www.ins.tn/",
            "ministry_finance": "https://www.finances.gov.tn/",
            "notes": "World Bank observations are comparable annual series. Latest national figures use higher-frequency INS releases and the Ministry of Finance debt bulletin; periods and definitions therefore differ.",
        },
    }
    payload = json.dumps(dashboard, ensure_ascii=False, separators=(",", ":"))
    (PROCESSED / "dashboard_data.json").write_text(payload, encoding="utf-8")
    (PUBLIC / "dashboard_data.json").write_text(payload, encoding="utf-8")
    (PUBLIC / "world_bank_indicators.csv").write_text(
        (PROCESSED / "world_bank_indicators.csv").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (PUBLIC / "tunisia_official_latest.csv").write_text(
        (PROCESSED / "tunisia_official_latest.csv").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (PROCESSED / "refresh_manifest.json").write_text(
        json.dumps(
            {
                "generated_at": generated_at,
                "world_bank_rows": len(wb),
                "national_latest_rows": len(national),
                "countries": list(COUNTRIES),
                "world_bank_indicators": list(INDICATORS),
                "national_sources": ["INS Tunisia", "Tunisia Ministry of Finance"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Prepared {len(wb):,} World Bank rows and {len(national):,} latest national observations.")


if __name__ == "__main__":
    main()
