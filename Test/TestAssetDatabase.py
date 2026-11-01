
import os
import sys
import tempfile
import unittest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "App"))
)

from AssetDatabase import AssetDatabase


class TestAssetDatabase(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = os.path.join(
            self.temp_dir.name, "TestAssets.db"
        )
        self.database = AssetDatabase(database_path)

        self.asset = {
            "id": "AST-000001",
            "name": "Village Hospital",
            "village": "Village A",
            "category": "hospital",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "owner_type": "government",
            "owner_name": "Health Department",
            "managing_authority": "District Health Office",
            "verification_status": "verified",
        }

    def tearDown(self):
        self.database.connection.close()
        self.temp_dir.cleanup()

    def test_database_creates_assets_table(self):
        result = self.database.connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = 'assets'"
        ).fetchone()

        self.assertIsNotNone(result)

    def test_save_asset(self):
        self.database.save_asset(self.asset)

        result = self.database.connection.execute(
            "SELECT * FROM assets WHERE id = ?",
            ("AST-000001",)
        ).fetchone()

        self.assertEqual(result["name"], "Village Hospital")
        self.assertEqual(result["village"], "Village A")
        self.assertEqual(result["category"], "hospital")

    def test_duplicate_asset_id_is_rejected(self):
        self.database.save_asset(self.asset)

        with self.assertRaises(Exception):
            self.database.save_asset(self.asset)

    def test_asset_survives_reopening_database(self):
        self.database.save_asset(self.asset)
        database_path = self.database.connection.execute(
            "PRAGMA database_list"
        ).fetchone()["file"]

        self.database.connection.close()
        self.database = AssetDatabase(database_path)

        result = self.database.connection.execute(
            "SELECT * FROM assets WHERE id = ?",
            ("AST-000001",)
        ).fetchone()

        self.assertEqual(result["name"], "Village Hospital")

    def test_optional_managing_authority_can_be_none(self):
        self.asset["managing_authority"] = None
        self.database.save_asset(self.asset)

        result = self.database.connection.execute(
            "SELECT managing_authority FROM assets WHERE id = ?",
            ("AST-000001",)
        ).fetchone()

        self.assertIsNone(result["managing_authority"])
    
    def test_get_asset(self):
        self.database.save_asset(self.asset)

        result = self.database.get_asset("AST-000001")

        self.assertEqual(result["name"], "Village Hospital")

    def test_get_missing_asset(self):
        result = self.database.get_asset("AST-999999")

        self.assertIsNone(result)

    def test_update_asset(self):
        self.database.save_asset(self.asset)

        updated = self.database.update_asset(
            "AST-000001",
            {"owner_name": "New Health Department"}
        )

        result = self.database.get_asset("AST-000001")

        self.assertTrue(updated)
        self.assertEqual(result["owner_name"], "New Health Department")
        self.assertEqual(result["id"], "AST-000001")

    def test_delete_asset(self):
        self.database.save_asset(self.asset)

        deleted = self.database.delete_asset("AST-000001")

        self.assertTrue(deleted)
        self.assertIsNone(self.database.get_asset("AST-000001"))
    
    def test_import_asset_successfully(self):
        asset = {
            "id": "AST-000101",
            "name": "Community Hospital",
            "village": "Village X",
            "category": "hospital",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "owner_type": "government",
            "owner_name": "Health Department",
            "managing_authority": None,
            "verification_status": "unverified",
        }

        result = self.database.import_asset(asset)

        self.assertTrue(result["success"])
        self.assertEqual(
            self.database.get_asset("AST-000101")["name"],
            "Community Hospital",
        )

    def test_import_rejects_duplicate_id(self):
        asset = {
            "id": "AST-000102",
            "name": "Primary School",
            "village": "Village X",
            "category": "school",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "owner_type": "government",
            "owner_name": "Education Department",
            "managing_authority": None,
            "verification_status": "unverified",
        }

        first_result = self.database.import_asset(asset)
        second_result = self.database.import_asset(asset)

        self.assertTrue(first_result["success"])
        self.assertFalse(second_result["success"])

    def test_import_rejects_invalid_asset(self):
        asset = {
            "id": "INVALID-ID",
            "name": "",
            "village": "Village X",
            "category": "hospital",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "owner_type": "government",
            "owner_name": "Health Department",
            "managing_authority": None,
            "verification_status": "unverified",
        }

        result = self.database.import_asset(asset)

        self.assertFalse(result["success"])
        self.assertIsNotNone(
            self.database.get_asset("INVALID-ID")
        ) if False else self.assertIsNone(
            self.database.get_asset("INVALID-ID")
        )


if __name__ == "__main__":
    unittest.main()
