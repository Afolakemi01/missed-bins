# Missed Bins: Ward Summary Pipeline

A Python pipeline that validates missed-bin collection reports and produces a per-ward summary for a council waste services team. The data is fictional.

## Business context

The Waste Services Manager needs to know which wards had the most missed-bin reports in a given week, so issues can be raised with the collection crews. Reports that cannot be used are returned to the contact centre with a reason, so they can be corrected.

## What the pipeline does

```
read CSV → validate each row → count valid reports per ward → write outputs
```

1. Reads `data/missed_bins.csv`.
2. Checks that every expected column is present and stops the run immediately if any are missing.
3. Validates each row against the rules below. The first rule a row fails decides its rejection reason.
4. Counts valid reports per ward, after cleaning ward names (`" otley "`, `"OTLEY"` → `"Otley"`).
5. Writes a sorted ward summary and a rejects file.
6. Logs row counts at each stage and checks that rows in = valid + rejected.

## Validation rules

| Order | Rule | Rejection reason |
|---|---|---|
| 1 | `report_id` is blank | `missing report_id` |
| 2 | `report_id` already seen (first copy kept) | `duplicate report_id` |
| 3 | `ward` is blank | `missing ward` |
| 4 | `bin_type` is not general, recycling, garden or food | `invalid bin_type` |
| 5 | A date is not a valid `YYYY-MM-DD` date | `invalid date` |
| 6 | `reported_date` is before `collection_date` | `reported before collection` |

## Outputs

| File | Contents |
|---|---|
| `output/ward_summary.csv` | `ward, missed_reports`, one row per ward, highest count first |
| `output/rejects.csv` | Rejected rows exactly as received, plus a `reason` column |

Result on the sample data: 22 rows read, 15 valid, 7 rejected.

| ward | missed_reports |
|---|---|
| Otley | 5 |
| Ilkley | 4 |
| Burley | 3 |
| Menston | 2 |
| Pool | 1 |

## Project structure

```
missed-bins/
├── data/missed_bins.csv
├── missed_bins/
│   ├── __init__.py
│   └── missed_bins.py
├── output/
├── tests/test_cleaning.py
└── README.md
```

## Setup and run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest ruff
python -m missed_bins.missed_bins
```

## Tests and linting

```bash
pytest
ruff check .
```

Tests cover the rejection rules, a valid row passing, and ward-name cleaning in the per-ward count.

## Design decisions

- **Fail fast on structure, isolate bad rows.** A missing column stops the run with a clear error. A bad row is rejected on its own without affecting the rest of the file.
- **Raw values in rejects.** The contact centre sees each report exactly as it arrived, so it can be found and corrected at source.
- **Strict date format.** Each parsed date is compared back to the original text, so only true `YYYY-MM-DD` values are accepted.
- **Clean before grouping.** Ward names are normalised before counting, so spelling variants of one ward are not split into separate groups.

## Limitations and future improvements

- File paths are hard-coded. They could move to configuration or command-line arguments.
- Logs go to the console only. A log file would support scheduled runs.
- The summary could break counts down further, for example by bin type.
