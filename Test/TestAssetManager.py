
import os
import sys
import tempfile
import unittest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "App"))
)

from AssetManager import AssetManager


class TestAssetManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = os.path.join(
            self.temp_dir.name, "TestAssets.db"
        )
        self.manager = AssetManager(database_path)

    def tearDown(self):
        self.manager.close()
        self.temp_dir.cleanup()

    def register_sample_asset(self, name="Government School",
                              village="Kallur", category="school"):
        return self.manager.add_asset(
            name, village, category,
            12.9716, 77.5946,
            "government", "Department of Education"
        )

    def test_first_id_is_generated(self):
        result = self.register_sample_asset()
        self.assertTrue(result["success"])
        self.assertEqual(result["asset"]["id"], "AST-000001")

    def test_ids_are_unique(self):
        first = self.register_sample_asset("School One")
        second = self.register_sample_asset("School Two")

        self.assertEqual(first["asset"]["id"], "AST-000001")
        self.assertEqual(second["asset"]["id"], "AST-000002")

    def test_invalid_asset_is_not_saved(self):
        result = self.manager.add_asset(
            "", "Kallur", "school",
            12.9716, 77.5946,
            "government", "Department of Education"
        )

        self.assertFalse(result["success"])
        self.assertEqual(self.manager.list_assets(), [])

    def test_failed_registration_does_not_consume_id(self):
        self.manager.add_asset(
            "", "Kallur", "school",
            12.9716, 77.5946,
            "government", "Department of Education"
        )

        result = self.register_sample_asset()
        self.assertEqual(result["asset"]["id"], "AST-000001")

    def test_update_owner_name(self):
        created = self.register_sample_asset()
        result = self.manager.update_owner_name(
            created["asset"]["id"], "New Department"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["asset"]["owner_name"], "New Department")
        self.assertEqual(result["asset"]["id"], "AST-000001")
        self.assertEqual(result["asset"]["name"], "Government School")

    def test_unknown_asset_cannot_be_updated(self):
        result = self.manager.update_owner_name(
            "AST-999999", "New Department"
        )
        self.assertFalse(result["success"])

    def test_search_by_village(self):
        self.register_sample_asset("School One", "Kallur")
        self.register_sample_asset("School Two", "Mysuru")

        results = self.manager.search_assets("Kallur")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["village"], "Kallur")

    def test_filter_by_category(self):
        self.register_sample_asset("Government School", category="school")
        self.register_sample_asset(
            "Village Hospital", category="hospital"
        )

        results = self.manager.filter_by_category("hospital")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Village Hospital")
    
    def test_asset_persists_after_reopening_manager(self):
        result = self.register_sample_asset()
        asset_id = result["asset"]["id"]

        database_path = self.manager.database.connection.execute(
            "PRAGMA database_list"
        ).fetchone()["file"]

        self.manager.close()

        reopened_manager = AssetManager(database_path)

        try:
            saved_asset = reopened_manager.get_asset(asset_id)
            self.assertIsNotNone(saved_asset)
            self.assertEqual(saved_asset["name"], "Government School")
        finally:
            reopened_manager.close()


if __name__ == "__main__":
    unittest.main()
