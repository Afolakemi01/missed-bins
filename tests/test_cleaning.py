from missed_bins.missed_bins import check_dates, check_missing_ward, count_by_ward


def test_missing_ward_is_rejected():
    row = {
        "report_id": "MB001",
        "ward": "",
        "bin_type": "general",
        "collection_date": "2026-11-02",
        "reported_date": "2026-11-02"
    }

    _record, reason = check_missing_ward(row)
    assert reason == "missing ward"

def test_reported_before_collection_is_rejected():
    row = {
            "report_id": "MB001",
            "ward": "Otley",
            "bin_type": "general",
            "collection_date": "2026-11-02",
            "reported_date": "2026-11-01"
        }
    _record, reason = check_dates(row)
    assert reason == "reported before collection"

def test_valid_row_passes():
    row = {
        "report_id": "MB001",
        "ward": "Otley",
        "bin_type": "general",
        "collection_date": "2026-11-02",
        "reported_date": "2026-11-03",
    }
    _record, reason = check_dates(row)
    assert reason is None

def test_count_by_ward():
    valid_rows = [
        {"ward": "Otley"},
        {"ward": "otley"},
        {"ward": " Otley "},
        {"ward": "Leeds"},
        {"ward": "Leeds"},
    ]

    result = count_by_ward(valid_rows)

    expected = {
        "Otley": 3,
        "Leeds": 2
    }

    assert result == expected

