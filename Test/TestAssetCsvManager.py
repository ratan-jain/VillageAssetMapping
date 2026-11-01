
import csv
import os
import sys
import tempfile
import unittest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "App"))
)

from AssetManager import AssetManager
from AssetCsvManager import AssetCsvManager


class TestAssetCsvManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        database_path = os.path.join(
            self.temp_dir.name, "TestAssets.db"
        )
        self.manager = AssetManager(database_path)
        self.csv_manager = AssetCsvManager(self.manager)

        self.manager.add_asset(
            "Village Hospital",
            "Village A",
            "hospital",
            12.9716,
            77.5946,
            "government",
            "Health Department",
        )

    def tearDown(self):
        self.manager.close()
        self.temp_dir.cleanup()

    def test_exports_asset_count(self):
        csv_path = os.path.join(self.temp_dir.name, "assets.csv")

        count = self.csv_manager.export_assets(csv_path)

        self.assertEqual(count, 1)

    def test_exports_correct_headers(self):
        csv_path = os.path.join(self.temp_dir.name, "assets.csv")

        self.csv_manager.export_assets(csv_path)

        with open(csv_path, "r", newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            expected_headers = [
                "id",
                "name",
                "village",
                "category",
                "latitude",
                "longitude",
                "owner_type",
                "owner_name",
                "managing_authority",
                "verification_status",
            ]

            self.assertEqual(reader.fieldnames, expected_headers)

    def test_exports_asset_data(self):
        csv_path = os.path.join(self.temp_dir.name, "assets.csv")

        self.csv_manager.export_assets(csv_path)

        with open(csv_path, "r", newline="", encoding="utf-8") as csv_file:
            rows = list(csv.DictReader(csv_file))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "Village Hospital")
        self.assertEqual(rows[0]["village"], "Village A")
        self.assertEqual(rows[0]["category"], "hospital")
        self.assertEqual(rows[0]["owner_name"], "Health Department")
    
    def test_imports_valid_csv(self):
        csv_path = os.path.join(self.temp_dir.name, "import.csv")

        with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([
                "id", "name", "village", "category",
                "latitude", "longitude", "owner_type",
                "owner_name", "managing_authority",
                "verification_status",
            ])
            writer.writerow([
                "AST-000101", "New Hospital", "Village B",
                "hospital", "13.0", "77.6", "government",
                "Health Department", "", "unverified",
            ])

        result = self.csv_manager.import_assets(csv_path)

        self.assertEqual(result["imported"], 1)
        self.assertEqual(result["errors"], [])
        self.assertEqual(
            self.manager.get_asset("AST-000101")["name"],
            "New Hospital",
        )

    def test_import_rejects_duplicate_id(self):
        csv_path = os.path.join(self.temp_dir.name, "duplicate.csv")

        with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([
                "id", "name", "village", "category",
                "latitude", "longitude", "owner_type",
                "owner_name", "managing_authority",
                "verification_status",
            ])
            writer.writerow([
                "AST-000001", "Duplicate Hospital", "Village B",
                "hospital", "13.0", "77.6", "government",
                "Health Department", "", "unverified",
            ])

        result = self.csv_manager.import_assets(csv_path)

        self.assertEqual(result["imported"], 0)
        self.assertEqual(len(result["errors"]), 1)

    def test_import_rejects_missing_headers(self):
        csv_path = os.path.join(self.temp_dir.name, "invalid.csv")

        with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["id", "name"])
            writer.writerow(["AST-000101", "Incomplete Hospital"])

        result = self.csv_manager.import_assets(csv_path)

        self.assertEqual(result["imported"], 0)
        self.assertEqual(
            result["errors"],
            ["CSV file is missing required columns."],
        )


if __name__ == "__main__":
    unittest.main()
