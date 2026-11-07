
import sqlite3

DATABASE_PATH = "VillageAssets.db"

connection = sqlite3.connect(DATABASE_PATH)
cursor = connection.cursor()

checks = {
    "Original OSM components":
        "SELECT COUNT(*) FROM geographical_components",

    "Grid assignments":
        "SELECT COUNT(*) FROM geographical_component_grid",

    "Facility classifications":
        "SELECT COUNT(*) FROM geographical_component_classifications",

    "Duplicate grid assignments":
        """
        SELECT COUNT(*)
        FROM (
            SELECT component_id
            FROM geographical_component_grid
            GROUP BY component_id
            HAVING COUNT(*) > 1
        )
        """,

    "Components without grid assignment":
        """
        SELECT COUNT(*)
        FROM geographical_components g
        LEFT JOIN geographical_component_grid a
            ON g.id = a.component_id
        WHERE a.component_id IS NULL
        """,

    "Components without classification":
        """
        SELECT COUNT(*)
        FROM geographical_components g
        LEFT JOIN geographical_component_classifications c
            ON g.id = c.component_id
        WHERE c.component_id IS NULL
        """,

    "Invalid grid references":
        """
        SELECT COUNT(*)
        FROM geographical_component_grid a
        LEFT JOIN geographical_components g
            ON a.component_id = g.id
        WHERE g.id IS NULL
        """,

    "Invalid classification references":
        """
        SELECT COUNT(*)
        FROM geographical_component_classifications c
        LEFT JOIN geographical_components g
            ON c.component_id = g.id
        WHERE g.id IS NULL
        """,
}

print("\nFINAL DATABASE INTEGRITY REPORT")
print("=" * 55)

for label, query in checks.items():
    cursor.execute(query)
    result = cursor.fetchone()[0]
    print(f"{label:<40} {result:>12,}")

connection.close()

print("\nIntegrity verification completed.")
