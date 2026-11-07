
import os
import sqlite3
import tempfile
import unittest

import geopandas as gpd
from shapely.geometry import box

from App.GridServiceAnalyzer import analyze_grid_services


class TestGridServiceAnalyzer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(
            self.temp_dir.name,
            "TestAssets.db"
        )

        connection = sqlite3.connect(self.database_path)
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE geographical_components (
                id TEXT PRIMARY KEY
            )
        """)

        cursor.execute("""
            CREATE TABLE geographical_component_grid (
                component_id TEXT PRIMARY KEY,
                grid_id TEXT,
                assignment_status TEXT,
                assignment_method TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE geographical_component_classifications (
                component_id TEXT PRIMARY KEY,
                source_id TEXT,
                service_group TEXT,
                service_type TEXT,
                confidence TEXT,
                review_status TEXT,
                classification_reason TEXT
            )
        """)

        components = [
            ("C1",),
            ("C2",),
            ("C3",),
            ("C4",),
        ]

        assignments = [
            ("C1", "GRID-001", "assigned", "test"),
            ("C2", "GRID-001", "assigned", "test"),
            ("C3", "GRID-001", "assigned", "test"),
            ("C4", "GRID-002", "assigned", "test"),
        ]

        classifications = [
            ("C1", "S1", "healthcare", "hospital",
             "high", "classified", "Test healthcare"),
            ("C2", "S2", "unclassified", "unclassified",
             "low", "needs_review", "Test review"),
            ("C3", "S3", "transport", "bus_station",
             "high", "classified", "Test transport"),
            ("C4", "S4", "unclassified", "unclassified",
             "low", "needs_review", "Test review"),
        ]

        cursor.executemany(
            "INSERT INTO geographical_components VALUES (?)",
            components
        )

        cursor.executemany(
            "INSERT INTO geographical_component_grid VALUES (?, ?, ?, ?)",
            assignments
        )

        cursor.executemany("""
            INSERT INTO geographical_component_classifications
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, classifications)

        connection.commit()
        connection.close()

        self.grid = gpd.GeoDataFrame(
            {
                "Grid_ID": [
                    "GRID-001",
                    "GRID-002",
                    "GRID-003",
                ],
            },
            geometry=[
                box(0, 0, 500, 500),
                box(500, 0, 1000, 500),
                box(1000, 0, 1500, 500),
            ],
            crs="EPSG:32643",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_analyzes_all_grid_cells(self):
        result = analyze_grid_services(
            self.database_path,
            self.grid
        )

        self.assertEqual(
            len(result["grid_results"]),
            3
        )

        self.assertEqual(
            result["summary"]["grid_cells"],
            3
        )

    def test_counts_classified_facilities(self):
        result = analyze_grid_services(
            self.database_path,
            self.grid
        )

        self.assertEqual(
            result["summary"]["classified_facilities"],
            2
        )

    def test_counts_service_groups(self):
        result = analyze_grid_services(
            self.database_path,
            self.grid
        )

        summary = result["summary"]

        self.assertEqual(summary["healthcare_total"], 1)
        self.assertEqual(summary["transport_total"], 1)
        self.assertEqual(summary["education_total"], 0)

    def test_identifies_potential_service_gaps(self):
        result = analyze_grid_services(
            self.database_path,
            self.grid
        )

        summary = result["summary"]

        self.assertEqual(
            summary["cells_with_mapped_services"],
            1
        )

        self.assertEqual(
            summary["cells_without_mapped_essential_services"],
            2
        )

    def test_preserves_empty_grid_cells(self):
        result = analyze_grid_services(
            self.database_path,
            self.grid
        )

        empty_cell = result["grid_results"].loc[
            result["grid_results"]["Grid_ID"] == "GRID-003"
        ].iloc[0]

        self.assertEqual(
            empty_cell["Total_OSM_Components"],
            0
        )

        self.assertTrue(
            empty_cell["Potential_Service_Gap"]
        )

    def test_counts_needs_review_records(self):
        result = analyze_grid_services(
            self.database_path,
            self.grid
        )

        self.assertEqual(
            result["grid_results"]["Needs_Review"].sum(),
            2
        )

    def test_rejects_invalid_grid_type(self):
        with self.assertRaises(TypeError):
            analyze_grid_services(
                self.database_path,
                []
            )

    def test_rejects_empty_grid(self):
        empty_grid = self.grid.iloc[0:0]

        with self.assertRaises(ValueError):
            analyze_grid_services(
                self.database_path,
                empty_grid
            )

    def test_rejects_duplicate_grid_ids(self):
        duplicate_grid = self.grid.copy()
        duplicate_grid.loc[1, "Grid_ID"] = "GRID-001"

        with self.assertRaises(ValueError):
            analyze_grid_services(
                self.database_path,
                duplicate_grid
            )

    def test_rejects_missing_database_tables(self):
        with tempfile.TemporaryDirectory() as directory:
            empty_database = os.path.join(
                directory,
                "Empty.db"
            )

            sqlite3.connect(empty_database).close()

            with self.assertRaises(RuntimeError):
                analyze_grid_services(
                    empty_database,
                    self.grid
                )


if __name__ == "__main__":
    unittest.main()
