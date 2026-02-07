# Earnings Call Transcripts Downloader (Version 1.1)

This tool downloads Motley Fool earnings call transcript pages from a list of URLs and saves the content as `.md` and `.txt` files.

## Version 1.1 Scope

Version 1.1 focuses on:
- Input: explicit URLs (args or a URL list file)
- Output: `.md` and `.txt`
- Filenames: `TICKER_YYYY_MM_DD_<TitleCore>.md/.txt`, whitespace removed and non-alphanumeric characters stripped
- Polite crawling: one request per second by default

## How It Works (Architecture)

1. **Input layer**
   - Accepts URLs passed as command-line arguments or from a file (`--file`, one URL per line).
2. **Fetch layer**
   - Requests the HTML with a clear User-Agent.
3. **Parse layer**
   - Extracts title from `h1` (fallback to `og:title`, then `<title>`).
   - Extracts body from `article` (fallback to `main`, then `body`) and keeps paragraph text.
4. **Normalize layer**
   - Derives ticker from URL slug.
   - Extracts date from URL path (`YYYY/MM/DD` → `YYYY_MM_DD`).
   - Builds a filename by stripping company name/ticker from the title and normalizing to underscores.
5. **Output layer**
   - Writes `.md` and `.txt` with title, source URL, and body.

## Usage

Install dependencies:

```bash
python3 -m pip install -r /Users/x/X_Github_Repos/Earnings_Call_Transcripts/requirements.txt
```

### Option A: Pass URLs directly

```bash
python3 /Users/x/X_Github_Repos/Earnings_Call_Transcripts/download_transcripts.py \
  https://www.fool.com/earnings/call-transcripts/2026/02/05/amazon-amzn-q4-2025-earnings-call-transcript/
```

### Option B: Use a URL list file

```bash
python3 /Users/x/X_Github_Repos/Earnings_Call_Transcripts/download_transcripts.py \
  --file /Users/x/X_Github_Repos/Earnings_Call_Transcripts/fool_com.txt
```

### Options

- `--outdir` Output directory (default: current directory)
- `--delay` Seconds to wait between requests (default: `1.0`)
- `--overwrite` Overwrite existing files

## Maintenance Goal (Version 1.1)

- Keep the script stable and predictable.
- Keep dependencies minimal.
- Avoid system-level installs.
- Any feature additions should preserve the V1 behavior by keeping `download_transcripts_v1.py` unchanged.

## V1 Backup

- `download_transcripts_v1.py` is a frozen copy of the V1 logic for rollback.

## Notes

- Respect `robots.txt` and the site’s terms of use.
- The parser is intentionally simple; if the site layout changes, update the parse rules.
