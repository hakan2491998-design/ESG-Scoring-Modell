# ESG Report Analyzer

A small Python analyzer for ESG reports. It reads supported files from the `esg reports` folder and writes ranked results to `rankings.json`.

## Setup

1. Install `uv` if you do not already have it:

```bash
python3 -m pip install uv
```

2. Initialize the project and install dependencies:

```bash
uv sync
```

## Usage

Place your `.pdf` ESG reports into the `esg reports` folder, then run:

```bash
uv run python doc.py
```

The script will create `esg reports` if needed and always save output to `rankings.json`.

## Methodology

The analyzer uses regex patterns to score ESG reports across predefined criteria.

- **0 points**: criterion not found.
- **50 points**: keyword found without quantitative disclosure.
- **100 points**: quantitative disclosure found within the keyword context.

The overall score is the average of all criteria.

## Supported file formats

- `.pdf` (requires `pymupdf`)

## Adding or updating criteria

Edit the `ESG_CRITERIA` dictionary in `doc.py`.
Each criterion needs:

- `keywords_regex`: pattern to detect the ESG topic.
- `units_regex`: pattern to detect quantitative disclosure.

Example:

```python
"energy": {
    "keywords_regex": r"(?i)\b(energy\s*consum\w+|Energieverbrauch\w+|Stromverbrauch\w+)\b",
    "units_regex": r"(?i)\b(kWh|MWh|GJ|%\s*energy\s*sav\w+)\b",
}
```
