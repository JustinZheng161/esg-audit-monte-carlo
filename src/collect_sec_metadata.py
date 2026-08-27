"""Fetch a small, auditable SEC EDGAR metadata snapshot for future calibration.

This script is intentionally not part of the synthetic Monte Carlo estimation. It
retrieves public company identifier and XBRL availability metadata from data.sec.gov,
keeps raw API responses outside the public repository, and writes a public manifest
with URLs and SHA-256 hashes only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
USER_AGENT = "esg-audit-monte-carlo-research/1.0 research@example.invalid"


def get_json(url: str) -> bytes:
    response = requests.get(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}, timeout=30)
    response.raise_for_status()
    return response.content


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", nargs="+", default=["AAPL", "MSFT", "AMZN", "JPM", "XOM"])
    parser.add_argument("--raw-dir", type=Path, default=ROOT.parent / "private" / "data" / "raw" / "sec")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data" / "public" / "sec_metadata_manifest.csv")
    args = parser.parse_args()
    args.raw_dir.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)

    ticker_payload = get_json(TICKERS_URL)
    tickers = json.loads(ticker_payload)
    by_ticker = {row["ticker"].upper(): row for row in tickers.values()}
    rows = []
    timestamp = datetime.now(timezone.utc).isoformat()
    for ticker in [t.upper() for t in args.tickers]:
        if ticker not in by_ticker:
            raise ValueError(f"Ticker not found in SEC mapping: {ticker}")
        item = by_ticker[ticker]
        cik = int(item["cik_str"])
        url = FACTS_URL.format(cik=cik)
        content = get_json(url)
        filename = args.raw_dir / f"CIK{cik:010d}_companyfacts.json"
        filename.write_bytes(content)
        rows.append({
            "retrieved_at_utc": timestamp,
            "ticker": ticker,
            "company_name": item["title"],
            "cik": f"{cik:010d}",
            "source_url": url,
            "raw_sha256": hashlib.sha256(content).hexdigest(),
            "raw_storage": "private/data/raw/sec/",
            "public_release": "metadata_only",
            "source": "U.S. SEC EDGAR Company Facts API",
        })
        time.sleep(0.12)  # Respect the SEC's fair-access expectation; below 10 requests/second.
    pd.DataFrame(rows).to_csv(args.manifest, index=False)
    print(f"Wrote {len(rows)} private SEC snapshots and one public manifest: {args.manifest}")


if __name__ == "__main__":
    main()
