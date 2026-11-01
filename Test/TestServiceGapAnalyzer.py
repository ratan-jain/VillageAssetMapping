
import os
import sys
import tempfile
import unittest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "App"))
)

from AssetManager import AssetManager
from ServiceGapAnalyzer import ServiceGapAnalyzer


class TestServiceGapAnalyzer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = os.path.join(
            self.temp_dir.name, "TestAssets.db"
        )
        self.manager = AssetManager(database_path)

        self.manager.add_asset(
            "Village Hospital", "Village A", "hospital",
            12.9716, 77.5946, "government", "Health Department"
        )
        self.manager.add_asset(
            "Remote Hospital", "Village C", "hospital",
            13.0716, 77.5946, "government", "Health Department"
        )

        self.analyzer = ServiceGapAnalyzer(self.manager)

    def tearDown(self):
        self.manager.close()
        self.temp_dir.cleanup()

    def test_village_within_range(self):
        result = self.analyzer.analyze_village(
            "Village A", 12.9716, 77.5946, "hospital", 5
        )
        self.assertEqual(result["status"], "within_range")
        self.assertEqual(result["distance_km"], 0)

    def test_potential_service_gap(self):
        result = self.analyzer.analyze_village(
            "Village B", 13.1716, 77.5946, "hospital", 5
        )
        self.assertEqual(result["status"], "potential_service_gap")

    def test_no_facility_found(self):
        result = self.analyzer.analyze_village(
            "Village A", 12.9716, 77.5946, "school", 5
        )
        self.assertEqual(result["status"], "no_facility_found")
        self.assertIsNone(result["nearest_asset"])
        self.assertIsNone(result["distance_km"])

    def test_rejects_empty_village_name(self):
        with self.assertRaises(ValueError):
            self.analyzer.analyze_village(
                "", 12.9716, 77.5946, "hospital", 5
            )

    def test_rejects_negative_distance_threshold(self):
        with self.assertRaises(ValueError):
            self.analyzer.analyze_village(
                "Village A", 12.9716, 77.5946, "hospital", -1
            )

    def test_rejects_boolean_distance_threshold(self):
        with self.assertRaises(ValueError):
            self.analyzer.analyze_village(
                "Village A", 12.9716, 77.5946, "hospital", True
            )


if __name__ == "__main__":
    unittest.main()
