import codecs
import csv
import io

from app.services.data_export import records_to_csv


def test_csv_has_bom_chinese_and_stable_columns():
    payload = records_to_csv([
        {
            "record_type": "饮食",
            "recorded_at": "2026-07-10 08:00:00",
            "name": "鸡蛋",
            "details": {"蛋白质_g": 12.6},
        }
    ])

    assert payload.startswith(codecs.BOM_UTF8)
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))
    assert rows[0]["record_type"] == "饮食"
    assert '"蛋白质_g": 12.6' in rows[0]["details"]
