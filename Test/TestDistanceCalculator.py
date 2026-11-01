
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "App"))

from DistanceCalculator import calculate_distance_km


class TestDistanceCalculator(unittest.TestCase):

    def test_same_point_has_zero_distance(self):
        distance = calculate_distance_km(
            12.9716, 77.5946,
            12.9716, 77.5946,
        )
        self.assertAlmostEqual(distance, 0.0, places=9)

    def test_distance_is_symmetric(self):
        distance_ab = calculate_distance_km(
            12.9716, 77.5946,
            12.9810, 77.6040,
        )
        distance_ba = calculate_distance_km(
            12.9810, 77.6040,
            12.9716, 77.5946,
        )
        self.assertAlmostEqual(distance_ab, distance_ba, places=9)

    def test_distance_is_positive(self):
        distance = calculate_distance_km(
            12.9716, 77.5946,
            12.9810, 77.6040,
        )
        self.assertGreater(distance, 0)
        self.assertLess(distance, 5)

    def test_invalid_latitude_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_distance_km(91, 0, 0, 0)

    def test_invalid_longitude_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_distance_km(0, 181, 0, 0)

    def test_boolean_coordinate_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_distance_km(True, 0, 0, 0)

    def test_nan_coordinate_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_distance_km(float("nan"), 0, 0, 0)


if __name__ == "__main__":
    unittest.main()
