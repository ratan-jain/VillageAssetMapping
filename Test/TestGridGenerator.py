
import sys
import unittest
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Polygon, box

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "App"))

from GridGenerator import generate_grid


class TestGridGenerator(unittest.TestCase):

    def setUp(self):
        self.boundary = gpd.GeoDataFrame(
            geometry=[box(0, 0, 20, 20)],
            crs="EPSG:32643",
        )

    def test_generates_expected_number_of_cells(self):
        grid = generate_grid(
            self.boundary,
            cell_size=10,
        )

        self.assertEqual(len(grid), 4)

    def test_generates_unique_grid_ids(self):
        grid = generate_grid(
            self.boundary,
            cell_size=10,
        )

        self.assertEqual(
            grid["Grid_ID"].nunique(),
            len(grid),
        )

    def test_grid_ids_are_deterministic(self):
        first_grid = generate_grid(
            self.boundary,
            cell_size=10,
        )

        second_grid = generate_grid(
            self.boundary,
            cell_size=10,
        )

        self.assertEqual(
            list(first_grid["Grid_ID"]),
            list(second_grid["Grid_ID"]),
        )

    def test_full_cells_have_complete_coverage(self):
        grid = generate_grid(
            self.boundary,
            cell_size=10,
        )

        self.assertTrue(
            (grid["Coverage_Fraction"] == 1.0).all()
        )

    def test_full_cell_area_is_correct(self):
        grid = generate_grid(
            self.boundary,
            cell_size=10,
        )

        self.assertTrue(
            (grid["Cell_Area_Sqm"] == 100).all()
        )

        self.assertTrue(
            (grid["Clipped_Area_Sqm"] == 100).all()
        )

    def test_clips_partial_boundary_cells(self):
        boundary = gpd.GeoDataFrame(
            geometry=[box(0, 0, 15, 10)],
            crs="EPSG:32643",
        )

        grid = generate_grid(
            boundary,
            cell_size=10,
        )

        self.assertEqual(len(grid), 2)

        partial_cells = grid[
            grid["Coverage_Fraction"] < 1
        ]

        self.assertEqual(len(partial_cells), 1)

        self.assertAlmostEqual(
            partial_cells.iloc[0]["Coverage_Fraction"],
            0.5,
        )

    def test_total_grid_area_matches_boundary_area(self):
        grid = generate_grid(
            self.boundary,
            cell_size=10,
        )

        self.assertAlmostEqual(
            grid["Clipped_Area_Sqm"].sum(),
            self.boundary.geometry.area.sum(),
        )

    def test_grid_uses_target_crs(self):
        grid = generate_grid(
            self.boundary,
            cell_size=10,
        )

        self.assertEqual(grid.crs.to_epsg(), 32643)

    def test_generated_geometries_are_valid(self):
        grid = generate_grid(
            self.boundary,
            cell_size=10,
        )

        self.assertTrue(grid.geometry.is_valid.all())

    def test_rejects_zero_cell_size(self):
        with self.assertRaises(ValueError):
            generate_grid(self.boundary, cell_size=0)

    def test_rejects_negative_cell_size(self):
        with self.assertRaises(ValueError):
            generate_grid(self.boundary, cell_size=-10)

    def test_rejects_boolean_cell_size(self):
        with self.assertRaises(ValueError):
            generate_grid(self.boundary, cell_size=True)

    def test_rejects_nan_cell_size(self):
        with self.assertRaises(ValueError):
            generate_grid(
                self.boundary,
                cell_size=float("nan"),
            )

    def test_rejects_invalid_boundary_geometry(self):
        invalid_polygon = Polygon([
            (0, 0),
            (10, 10),
            (0, 10),
            (10, 0),
            (0, 0),
        ])

        boundary = gpd.GeoDataFrame(
            geometry=[invalid_polygon],
            crs="EPSG:32643",
        )

        with self.assertRaises(ValueError):
            generate_grid(boundary, cell_size=10)

    def test_rejects_missing_boundary_file(self):
        with self.assertRaises(FileNotFoundError):
            generate_grid("NonExistentBoundary.geojson")


if __name__ == "__main__":
    unittest.main()
