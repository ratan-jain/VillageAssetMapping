
import os
import sys
import tempfile
import unittest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "App"))
)

from AssetManager import AssetManager
from NearbyAssetFinder import NearbyAssetFinder


class TestNearbyAssetFinder(unittest.TestCase):

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
            "Community Hospital", "Village A", "hospital",
            12.9816, 77.5946, "community", "Village Committee"
        )
        self.manager.add_asset(
            "Village School", "Village A", "school",
            12.9717, 77.5946, "government", "Education Department"
        )

        self.finder = NearbyAssetFinder(self.manager)

    def tearDown(self):
        self.manager.close()
        self.temp_dir.cleanup()

    def test_finds_nearby_assets(self):
        results = self.finder.find_nearby_assets(
            12.9716, 77.5946, 2
        )
        self.assertEqual(len(results), 3)

    def test_filters_by_category(self):
        results = self.finder.find_nearby_assets(
            12.9716, 77.5946, 2, category="hospital"
        )
        self.assertEqual(len(results), 2)
        self.assertTrue(
            all(asset["category"] == "hospital" for asset in results)
        )

    def test_nearest_asset_comes_first(self):
        results = self.finder.find_nearby_assets(
            12.9716, 77.5946, 2
        )
        distances = [asset["distance_km"] for asset in results]
        self.assertEqual(distances, sorted(distances))

    def test_excludes_assets_outside_radius(self):
        results = self.finder.find_nearby_assets(
            12.9716, 77.5946, 0
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Village Hospital")

    def test_rejects_negative_radius(self):
        with self.assertRaises(ValueError):
            self.finder.find_nearby_assets(
                12.9716, 77.5946, -1
            )

    def test_rejects_infinite_radius(self):
        with self.assertRaises(ValueError):
            self.finder.find_nearby_assets(
                12.9716, 77.5946, float("inf")
            )

    def test_rejects_boolean_radius(self):
        with self.assertRaises(ValueError):
            self.finder.find_nearby_assets(
                12.9716, 77.5946, True
            )


if __name__ == "__main__":
    unittest.main()
