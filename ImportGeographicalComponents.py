
import csv
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
CSV_PATH = PROJECT_ROOT / "BengaluruUrbanComponents.csv"
DATABASE_PATH = PROJECT_ROOT / "VillageAssets.db"

BATCH_SIZE = 5000

COLUMNS = [
    "id", "name", "village", "category",
    "latitude", "longitude", "owner_type", "owner_name",
    "managing_authority", "verification_status",
    "source", "source_id", "source_url", "osm_type",
    "component_type", "tags_json", "geometry_method"
]


def create_table(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS geographical_components (
            id TEXT PRIMARY KEY,
            name TEXT,
            village TEXT,
            category TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            owner_type TEXT,
            owner_name TEXT,
            managing_authority TEXT,
            verification_status TEXT,
            source TEXT,
            source_id TEXT NOT NULL UNIQUE,
            source_url TEXT,
            osm_type TEXT,
            component_type TEXT,
            tags_json TEXT,
            geometry_method TEXT
        )
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_geo_category
        ON geographical_components(category)
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_geo_coordinates
        ON geographical_components(latitude, longitude)
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_geo_name
        ON geographical_components(name)
    """)


def import_components():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    connection = sqlite3.connect(DATABASE_PATH)

    imported = 0
    skipped = 0
    invalid = 0
    batch = []

    insert_sql = """
        INSERT OR IGNORE INTO geographical_components (
            id, name, village, category, latitude, longitude,
            owner_type, owner_name, managing_authority,
            verification_status, source, source_id, source_url,
            osm_type, component_type, tags_json, geometry_method
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    try:
        create_table(connection)

        with open(CSV_PATH, encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            if reader.fieldnames != COLUMNS:
                raise ValueError(
                    f"Unexpected CSV columns: {reader.fieldnames}"
                )

            for row in reader:
                try:
                    latitude = float(row["latitude"])
                    longitude = float(row["longitude"])

                    if not (
                        -90 <= latitude <= 90
                        and -180 <= longitude <= 180
                    ):
                        invalid += 1
                        continue

                    if not row["id"] or not row["source_id"]:
                        invalid += 1
                        continue

                    batch.append((
                        row["id"],
                        row["name"],
                        row["village"],
                        row["category"],
                        latitude,
                        longitude,
                        row["owner_type"],
                        row["owner_name"],
                        row["managing_authority"],
                        row["verification_status"],
                        row["source"],
                        row["source_id"],
                        row["source_url"],
                        row["osm_type"],
                        row["component_type"],
                        row["tags_json"],
                        row["geometry_method"],
                    ))

                except (TypeError, ValueError):
                    invalid += 1
                    continue

                if len(batch) >= BATCH_SIZE:
                    before = connection.total_changes
                    connection.executemany(insert_sql, batch)
                    imported += connection.total_changes - before
                    skipped += len(batch) - (
                        connection.total_changes - before
                    )
                    batch.clear()

            if batch:
                before = connection.total_changes
                connection.executemany(insert_sql, batch)
                inserted = connection.total_changes - before
                imported += inserted
                skipped += len(batch) - inserted

        connection.commit()

        total = connection.execute(
            "SELECT COUNT(*) FROM geographical_components"
        ).fetchone()[0]

        print("\nIMPORT COMPLETED")
        print("------------------------------")
        print(f"New records imported: {imported:,}")
        print(f"Duplicates skipped:   {skipped:,}")
        print(f"Invalid records:      {invalid:,}")
        print(f"Total database rows:  {total:,}")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    import_components()
