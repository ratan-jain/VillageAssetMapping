
import os
import sys
import tempfile
import unittest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "App"))
)

from AssetManager import AssetManager
from BatchServiceGapAnalyzer import BatchServiceGapAnalyzer


class TestBatchServiceGapAnalyzer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = os.path.join(
            self.temp_dir.name, "TestAssets.db"
        )
        self.manager = AssetManager(database_path)

        self.manager.add_asset(
            "Village Hospital",
            "Village A",
            "hospital",
            12.9716,
            77.5946,
            "government",
            "Health Department",
        )

        self.manager.add_asset(
            "Remote Hospital",
            "Village C",
            "hospital",
            13.0716,
            77.5946,
            "government",
            "Health Department",
        )

        self.batch_analyzer = BatchServiceGapAnalyzer(self.manager)

    def tearDown(self):
        self.manager.close()
        self.temp_dir.cleanup()

    def test_analyzes_multiple_villages(self):
        villages = [
            {
                "name": "Village A",
                "latitude": 12.9716,
                "longitude": 77.5946,
            },
            {
                "name": "Village B",
                "latitude": 13.1716,
                "longitude": 77.5946,
            },
        ]

        results = self.batch_analyzer.analyze_villages(
            villages, "hospital", 5
        )

        self.assertEqual(len(results), 2)

    def test_identifies_different_service_statuses(self):
        villages = [
            {
                "name": "Village A",
                "latitude": 12.9716,
                "longitude": 77.5946,
            },
            {
                "name": "Village B",
                "latitude": 13.1716,
                "longitude": 77.5946,
            },
        ]

        results = self.batch_analyzer.analyze_villages(
            villages, "hospital", 5
        )

        self.assertEqual(results[0]["status"], "within_range")
        self.assertEqual(
            results[1]["status"], "potential_service_gap"
        )

    def test_empty_village_list_returns_empty_results(self):
        results = self.batch_analyzer.analyze_villages(
            [], "hospital", 5
        )

        self.assertEqual(results, [])

    def test_no_matching_facilities(self):
        villages = [
            {
                "name": "Village A",
                "latitude": 12.9716,
                "longitude": 77.5946,
            }
        ]

        results = self.batch_analyzer.analyze_villages(
            villages, "school", 5
        )

        self.assertEqual(
            results[0]["status"], "no_facility_found"
        )


if __name__ == "__main__":
    unittest.main()
