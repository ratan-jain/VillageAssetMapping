
import sqlite3
import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import box

from App.AssetGridAssigner import assign_components_to_grid


class TestAssetGridAssigner(unittest.TestCase):

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temp_directory.name) / "TestDatabase.db"
        )

        self.transformer = Transformer.from_crs(
            "EPSG:32643",
            "EPSG:4326",
            always_xy=True
        )

        self.grid = gpd.GeoDataFrame(
            {
                "Grid_ID": ["GRID-A", "GRID-B"],
                "geometry": [
                    box(500000, 1450000, 500500, 1450500),
                    box(500500, 1450000, 501000, 1450500)
                ]
            },
            crs="EPSG:32643"
        )

        self._create_database()

    def tearDown(self):
        self.temp_directory.cleanup()

    def _create_database(self):
        connection = sqlite3.connect(self.database_path)

        connection.execute("""
            CREATE TABLE geographical_components (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL UNIQUE,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL
            )
        """)

        connection.commit()
        connection.close()

    def _add_component(self, component_id, x, y):
        longitude, latitude = self.transformer.transform(x, y)

        connection = sqlite3.connect(self.database_path)

        connection.execute("""
            INSERT INTO geographical_components
            (id, source_id, latitude, longitude)
            VALUES (?, ?, ?, ?)
        """, (
            component_id,
            f"SOURCE-{component_id}",
            latitude,
            longitude
        ))

        connection.commit()
        connection.close()

    def _get_assignments(self):
        connection = sqlite3.connect(self.database_path)

        rows = connection.execute("""
            SELECT component_id, grid_id, assignment_status
            FROM geographical_component_grid
            ORDER BY component_id
        """).fetchall()

        connection.close()
        return rows

    def test_assigns_points_to_correct_cells(self):
        self._add_component("A", 500250, 1450250)
        self._add_component("B", 500750, 1450250)

        result = assign_components_to_grid(
            self.database_path,
            self.grid,
            batch_size=1
        )

        assignments = self._get_assignments()

        self.assertEqual(result["total_processed"], 2)
        self.assertEqual(result["assigned"], 2)
        self.assertEqual(result["outside_grid"], 0)

        self.assertEqual(assignments[0][1], "GRID-A")
        self.assertEqual(assignments[1][1], "GRID-B")

    def test_marks_outside_points(self):
        self._add_component("OUTSIDE", 502000, 1450250)

        result = assign_components_to_grid(
            self.database_path,
            self.grid
        )

        self.assertEqual(result["outside_grid"], 1)

        assignments = self._get_assignments()

        self.assertIsNone(assignments[0][1])
        self.assertEqual(assignments[0][2], "outside_grid")

    def test_resolves_shared_boundary_deterministically(self):
        self._add_component("BOUNDARY", 500500, 1450250)

        result = assign_components_to_grid(
            self.database_path,
            self.grid
        )

        assignments = self._get_assignments()

        self.assertEqual(assignments[0][1], "GRID-A")
        self.assertEqual(
            result["boundary_duplicate_matches"], 1
        )

    def test_every_component_has_one_assignment(self):
        self._add_component("A", 500250, 1450250)
        self._add_component("B", 500750, 1450250)
        self._add_component("C", 502000, 1450250)

        assign_components_to_grid(
            self.database_path,
            self.grid
        )

        connection = sqlite3.connect(self.database_path)

        total = connection.execute("""
            SELECT COUNT(*)
            FROM geographical_component_grid
        """).fetchone()[0]

        unique_ids = connection.execute("""
            SELECT COUNT(DISTINCT component_id)
            FROM geographical_component_grid
        """).fetchone()[0]

        connection.close()

        self.assertEqual(total, 3)
        self.assertEqual(unique_ids, 3)

    def test_rerunning_replaces_previous_assignments(self):
        self._add_component("A", 500250, 1450250)

        assign_components_to_grid(
            self.database_path,
            self.grid
        )

        assign_components_to_grid(
            self.database_path,
            self.grid
        )

        assignments = self._get_assignments()

        self.assertEqual(len(assignments), 1)

    def test_rejects_invalid_batch_size(self):
        with self.assertRaises(ValueError):
            assign_components_to_grid(
                self.database_path,
                self.grid,
                batch_size=0
            )

    def test_rejects_missing_database(self):
        missing_path = (
            Path(self.temp_directory.name) / "Missing.db"
        )

        with self.assertRaises(FileNotFoundError):
            assign_components_to_grid(
                missing_path,
                self.grid
            )


if __name__ == "__main__":
    unittest.main()
