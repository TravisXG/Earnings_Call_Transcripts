#!/usr/bin/env python3

import argparse
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


USER_AGENT = "Mozilla/5.0 (compatible; TranscriptDownloader/1.0; +https://www.fool.com/)"


def read_urls(args):
    urls = []
    if args.file:
        path = Path(args.file)
        if not path.exists():
            raise FileNotFoundError(f"URL list file not found: {path}")
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
    urls.extend(args.urls or [])
    deduped = []
    seen = set()
    for u in urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped


def extract_ticker_from_slug(slug):
    tokens = [t for t in slug.split("-") if t]
    for t in tokens:
        t_low = t.lower()
        if t_low in {"q1", "q2", "q3", "q4"}:
            continue
        if re.fullmatch(r"[a-zA-Z]{1,5}", t):
            return t.upper()
    return "UNKNOWN"


def extract_title_and_body(html):
    soup = BeautifulSoup(html, "html.parser")

    # Title: prefer h1, then og:title, then title tag
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        title = h1.get_text(strip=True)
    else:
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            title = og["content"].strip()
        elif soup.title and soup.title.get_text(strip=True):
            title = soup.title.get_text(strip=True)
        else:
            title = "Earnings Call Transcript"

    # Body: prefer article tag, then main, else entire body
    container = soup.find("article") or soup.find("main") or soup.body
    if not container:
        return title, ""

    # Remove scripts/styles and other non-content tags
    for tag in container.find_all(["script", "style", "noscript", "svg", "form", "nav", "header", "footer"]):
        tag.decompose()

    paragraphs = [p.get_text(" ", strip=True) for p in container.find_all("p")]
    paragraphs = [p for p in paragraphs if p]

    if paragraphs:
        body = "\n\n".join(paragraphs)
    else:
        # Fallback to all text
        body = container.get_text("\n", strip=True)

    return title, body


def normalize_filename(ticker, title):
    # Remove leading company name and optional ticker from title, if present
    # Example: "Amazon (AMZN) Q4 2025 Earnings Call Transcript" -> "Q4 2025 Earnings Call Transcript"
    cleaned = title
    cleaned = re.sub(r"^.*?\(%s\)\s*" % re.escape(ticker), "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^.*?\b%s\b\s*" % re.escape(ticker), "", cleaned, flags=re.IGNORECASE)

    # Replace spaces with underscores, remove non-alnum/underscore
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")

    if not cleaned:
        cleaned = "Earnings_Call_Transcript"

    return f"{ticker}_{cleaned}.md"


def fetch(url):
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def main():
    parser = argparse.ArgumentParser(description="Download earnings call transcripts from Motley Fool URLs.")
    parser.add_argument("urls", nargs="*", help="Transcript URLs")
    parser.add_argument("--file", help="Path to file with one URL per line")
    parser.add_argument("--outdir", default=".", help="Output directory (default: current directory)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    urls = read_urls(args)
    if not urls:
        print("No URLs provided. Use arguments or --file.")
        return 2

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for i, url in enumerate(urls, start=1):
        try:
            parsed = urlparse(url)
            slug = Path(parsed.path).name or Path(parsed.path).parent.name
            ticker = extract_ticker_from_slug(slug)

            html = fetch(url)
            title, body = extract_title_and_body(html)

            filename = normalize_filename(ticker, title)
            stem = Path(filename).stem
            md_path = outdir / f"{stem}.md"
            txt_path = outdir / f"{stem}.txt"

            if not args.overwrite:
                all_exist = all(p.exists() for p in [md_path, txt_path])
                if all_exist:
                    print(f"[{i}/{len(urls)}] Skipped (exists): {md_path.name}")
                    continue

            md = f"# {title}\n\nSource: {url}\n\n{body}\n"
            txt = f"{title}\n\nSource: {url}\n\n{body}\n"

            md_path.write_text(md, encoding="utf-8")
            txt_path.write_text(txt, encoding="utf-8")

            print(f"[{i}/{len(urls)}] Saved: {md_path.name}")

        except Exception as exc:
            print(f"[{i}/{len(urls)}] Failed: {url}\n  {exc}")

        if i < len(urls):
            time.sleep(args.delay)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
