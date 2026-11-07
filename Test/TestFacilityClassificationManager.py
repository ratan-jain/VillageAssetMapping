
import sqlite3
import tempfile
import unittest
from pathlib import Path

from App.FacilityClassificationManager import classify_all_components


class TestFacilityClassificationManager(unittest.TestCase):

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temp_directory.name) / "TestDatabase.db"
        )

        connection = sqlite3.connect(self.database_path)

        connection.execute("""
            CREATE TABLE geographical_components (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL UNIQUE,
                category TEXT,
                component_type TEXT,
                tags_json TEXT,
                name TEXT
            )
        """)

        records = [
            (
                "OSM-1", "SOURCE-1", "hospital", "hospital",
                '{"healthcare": "hospital"}', "General Hospital"
            ),
            (
                "OSM-2", "SOURCE-2", "school", "yes",
                '{"amenity": "school"}', "Government School"
            ),
            (
                "OSM-3", "SOURCE-3", "public_facility", "yes",
                '{"amenity": "police"}', "Police Station"
            ),
            (
                "OSM-4", "SOURCE-4", "public_facility", "fixme",
                '{"amenity": "fixme", "fixme:type": "dental"}',
                "Dental Clinic"
            ),
            (
                "OSM-5", "SOURCE-5", "other", "yes",
                '{"amenity": "yes"}', "Unknown Facility"
            )
        ]

        connection.executemany("""
            INSERT INTO geographical_components (
                id, source_id, category,
                component_type, tags_json, name
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, records)

        connection.commit()
        connection.close()

    def tearDown(self):
        self.temp_directory.cleanup()

    def _query(self, sql):
        connection = sqlite3.connect(self.database_path)
        try:
            return connection.execute(sql).fetchall()
        finally:
            connection.close()

    def test_processes_all_components(self):
        result = classify_all_components(
            self.database_path,
            batch_size=2
        )

        self.assertEqual(result["total_processed"], 5)
        self.assertEqual(result["classified"], 3)
        self.assertEqual(result["needs_review"], 2)

    def test_stores_correct_classifications(self):
        classify_all_components(self.database_path, batch_size=2)

        rows = self._query("""
            SELECT component_id, service_group, service_type
            FROM geographical_component_classifications
            ORDER BY component_id
        """)

        self.assertEqual(rows[0], ("OSM-1", "healthcare", "hospital"))
        self.assertEqual(rows[1], ("OSM-2", "education", "school"))
        self.assertEqual(rows[2], ("OSM-3", "emergency", "police_station"))

    def test_preserves_uncertain_records(self):
        classify_all_components(self.database_path)

        rows = self._query("""
            SELECT component_id, review_status
            FROM geographical_component_classifications
            WHERE review_status = 'needs_review'
            ORDER BY component_id
        """)

        self.assertEqual(
            rows,
            [("OSM-4", "needs_review"), ("OSM-5", "needs_review")]
        )

    def test_rerunning_does_not_duplicate_results(self):
        classify_all_components(self.database_path, batch_size=2)
        classify_all_components(self.database_path, batch_size=3)

        rows = self._query("""
            SELECT COUNT(*)
            FROM geographical_component_classifications
        """)

        self.assertEqual(rows[0][0], 5)

    def test_original_data_is_unchanged(self):
        before = self._query("""
            SELECT *
            FROM geographical_components
            ORDER BY id
        """)

        classify_all_components(self.database_path)

        after = self._query("""
            SELECT *
            FROM geographical_components
            ORDER BY id
        """)

        self.assertEqual(before, after)

    def test_rejects_invalid_batch_size(self):
        with self.assertRaises(ValueError):
            classify_all_components(
                self.database_path,
                batch_size=0
            )

    def test_rejects_missing_database(self):
        missing = Path(self.temp_directory.name) / "Missing.db"

        with self.assertRaises(FileNotFoundError):
            classify_all_components(missing)

    def test_service_group_counts(self):
        result = classify_all_components(self.database_path)

        counts = result["service_group_counts"]

        self.assertEqual(counts["healthcare"], 1)
        self.assertEqual(counts["education"], 1)
        self.assertEqual(counts["emergency"], 1)
        self.assertEqual(counts["unclassified"], 2)


if __name__ == "__main__":
    unittest.main()
