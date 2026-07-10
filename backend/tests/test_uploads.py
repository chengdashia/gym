from datetime import datetime, timedelta
import io
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import Image

from app.services.uploads import (
    cleanup_expired_uploads,
    finalize_upload,
    validate_image_bytes,
)


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args):
        return self

    def all(self):
        return self.rows

    def first(self):
        return self.rows[0] if self.rows else None


class FakeSession:
    def __init__(self, rows, events=None):
        self.rows = rows
        self.events = events if events is not None else []

    def query(self, model):
        return FakeQuery(self.rows)

    def delete(self, row):
        self.events.append(("delete", row.id))

    def commit(self):
        self.events.append(("commit", None))

    def rollback(self):
        self.events.append(("rollback", None))


class UploadTest(unittest.TestCase):
    def test_rejects_fake_png(self):
        with self.assertRaises(ValueError):
            validate_image_bytes(b"not an image", ".png")

    def test_accepts_real_png(self):
        contents = io.BytesIO()
        Image.new("RGB", (1, 1)).save(contents, format="PNG")

        self.assertEqual(validate_image_bytes(contents.getvalue(), ".png"), "png")

    def test_expired_cleanup_commits_database_delete_before_disk_delete(self):
        events = []
        upload = SimpleNamespace(
            id=3,
            is_temporary=1,
            expired_at=datetime.utcnow() - timedelta(seconds=1),
            file_url="/static/expired.png",
        )
        db = FakeSession([upload], events)

        with patch(
            "app.services.uploads.delete_local_file",
            side_effect=lambda file_url: events.append(("disk", file_url)),
        ):
            cleanup_expired_uploads(db)

        self.assertEqual(
            events,
            [("delete", 3), ("commit", None), ("disk", "/static/expired.png")],
        )

    def test_finalize_saved_upload_marks_it_permanent(self):
        upload = SimpleNamespace(
            id=4,
            user_id=9,
            file_url="/static/saved.png",
            is_temporary=1,
            usage_type="food_recognition",
            expired_at=datetime.utcnow(),
        )
        db = FakeSession([upload])

        image_url, delete_url = finalize_upload(db, 9, 4, keep=True)

        self.assertEqual(image_url, "/static/saved.png")
        self.assertIsNone(delete_url)
        self.assertEqual(upload.is_temporary, 0)
        self.assertEqual(upload.usage_type, "diet_record")
        self.assertIsNone(upload.expired_at)

    def test_finalize_discarded_upload_deletes_database_row(self):
        upload = SimpleNamespace(
            id=5,
            user_id=9,
            file_url="/static/discarded.png",
        )
        db = FakeSession([upload])

        image_url, delete_url = finalize_upload(db, 9, 5, keep=False)

        self.assertIsNone(image_url)
        self.assertEqual(delete_url, "/static/discarded.png")
        self.assertEqual(db.events, [("delete", 5)])

    def test_finalize_rejects_another_users_upload(self):
        upload = SimpleNamespace(
            id=6,
            user_id=10,
            file_url="/static/foreign.png",
        )
        db = FakeSession([upload])

        with self.assertRaises(ValueError):
            finalize_upload(db, 9, 6, keep=True)


if __name__ == "__main__":
    unittest.main()
