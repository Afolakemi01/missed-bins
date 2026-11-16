import csv
import logging
from datetime import date

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s, %(levelname)s, %(message)s"
)

logger = logging.getLogger(__name__)

EXPECTED = {"report_id", "ward", "bin_type", "collection_date", "reported_date"}


def check_field(record):
    keys = set(record)
    missing = EXPECTED - keys

    if missing:
        logger.critical("missing field!")
        raise ValueError(f"missing columns: {missing}")

    return (record, None)


def check_missing_id(record):
    cleaned = {key: value.strip() for key, value in record.items()}

    if cleaned["report_id"] == "":
        return (record, "missing report_id")

    return (cleaned, None)


def check_duplicate(record, seen):
    if record["report_id"] in seen:
        return (record, "duplicate report_id")

    seen.add(record["report_id"])
    return (record, None)


def check_missing_ward(record):
    if record["ward"] == "":
        return (record, "missing ward")

    return (record, None)


def check_bin_type(record):
    bins = ["general", "recycling", "garden", "food"]

    record["bin_type"] = record["bin_type"].strip().lower()

    if record["bin_type"] not in bins:
        return (record, "invalid bin_type")
    return (record, None)


def check_dates(record):
    try:
        collection_date = date.fromisoformat(record["collection_date"])

        if collection_date.isoformat() != record["collection_date"]:
            return (record, "invalid date")

    except ValueError:
        return (record, "invalid date")

    try:
        reported_date = date.fromisoformat(record["reported_date"])

        if reported_date.isoformat() != record["reported_date"]:
            return (record, "invalid date")

    except ValueError:
        return (record, "invalid date")

    if reported_date < collection_date:
        return (record, "reported before collection")

    parsed = {
        "report_id": record["report_id"],
        "ward": record["ward"].title(),
        "bin_type": record["bin_type"],
        "collection_date": collection_date,
        "reported_date": reported_date,
    }
    return (parsed, None)


def validate(row, seen):
    record, reason = check_field(row)
    if reason is not None:
        return (row, reason)

    record, reason = check_missing_id(record)
    if reason is not None:
        return (record, reason)

    record, reason = check_duplicate(record, seen)
    if reason is not None:
        return (record, reason)

    record, reason = check_missing_ward(record)
    if reason is not None:
        return (record, reason)

    record, reason = check_bin_type(record)
    if reason is not None:
        return (record, reason)

    record, reason = check_dates(record)
    if reason is not None:
        return (record, reason)

    return (record, None)


def count_by_ward(valid_rows):
    counts = {}
    for row in valid_rows:
        ward = row["ward"].strip().title()
        counts[ward] = counts.get(ward, 0) + 1
    return counts


def read_file(path, seen):
    rows_in = 0
    rows_rejected = 0
    cleaned_rows = 0

    rejects = []
    cleaned = []

    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows_in += 1
            record, reason = validate(row, seen)
            if reason is not None:
                reject_record = {**row, "reason": reason}
                rejects.append(reject_record)
                rows_rejected += 1

            else:
                cleaned.append(record)
                cleaned_rows += 1

    assert rows_in == rows_rejected + cleaned_rows, (
        f"assertion failed: rows do not match: rows_in:{rows_in}, rejected_rows:{rows_rejected}, cleaned_rows{cleaned_rows}"
    )
    return cleaned, rejects, rows_in, rows_rejected, cleaned_rows


def write_summary(counts, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["ward", "missed_reports"]

        clean_writer = csv.DictWriter(f, fieldnames=fieldnames)
        clean_writer.writeheader()
        counts = sorted(counts.items(), key=lambda pair: pair[1], reverse=True)
        rows = [{"ward": ward, "missed_reports": count} for ward, count in counts]
        clean_writer.writerows(rows)
        return len(rows)


def write_rejects(rejects, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "report_id",
            "ward",
            "bin_type",
            "collection_date",
            "reported_date",
            "reason",
        ]
        reject_writer = csv.DictWriter(f, fieldnames=fieldnames)
        reject_writer.writeheader()
        reject_writer.writerows(rejects)
    return len(rejects)


def main():
    logger.info("run started")
    seen = set()

    cleaned, rejects, rows_in, rows_rejected, cleaned_rows = read_file(
        "data/missed_bins.csv", seen
    )
    logger.info(
        "read %s rows, cleaned %s rows, rejected %s rows",
        rows_in,
        cleaned_rows,
        rows_rejected,
    )

    wards = count_by_ward(cleaned)
    logger.info("counting wards")

    number_of_wards = write_summary(wards, "output/ward_summary.csv")
    logger.info("wrote %s rows to output/ward_summary.csv", number_of_wards)

    write_rejects(rejects, "output/rejects.csv")
    logger.info("wrote %s rows to output/rejects.csv", len(rejects))

    logger.info("run finished")
    return f" reconciliation: rows_in: {rows_in} == rejected_rows: {rows_rejected} + cleaned_rows: {cleaned_rows}"


if __name__ == "__main__":
    try:
        result = main()
    except Exception:
        logger.exception("run failed")
        raise
    else:
        print(result)
