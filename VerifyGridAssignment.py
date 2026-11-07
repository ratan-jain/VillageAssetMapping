import sqlite3

DATABASE_PATH = "VillageAssets.db"

connection = sqlite3.connect(DATABASE_PATH)

try:
    queries = {
        "Original geographical records": """
            SELECT COUNT(*)
            FROM geographical_components
        """,

        "Assignment records": """
            SELECT COUNT(*)
            FROM geographical_component_grid
        """,

        "Successfully assigned": """
            SELECT COUNT(*)
            FROM geographical_component_grid
            WHERE assignment_status = 'assigned'
        """,

        "Outside grid": """
            SELECT COUNT(*)
            FROM geographical_component_grid
            WHERE assignment_status = 'outside_grid'
        """,

        "Missing grid IDs": """
            SELECT COUNT(*)
            FROM geographical_component_grid
            WHERE grid_id IS NULL
        """,

        "Duplicate component IDs": """
            SELECT COUNT(*) - COUNT(DISTINCT component_id)
            FROM geographical_component_grid
        """,

        "Duplicate source IDs": """
            SELECT COUNT(*) - COUNT(DISTINCT source_id)
            FROM geographical_component_grid
        """,

        "Components without assignments": """
            SELECT COUNT(*)
            FROM geographical_components AS g
            LEFT JOIN geographical_component_grid AS a
                ON g.id = a.component_id
            WHERE a.component_id IS NULL
        """
    }

    print("\nGRID ASSIGNMENT INTEGRITY CHECK")
    print("=" * 45)

    for title, query in queries.items():
        result = connection.execute(query).fetchone()[0]
        print(f"{title}: {result:,}")

    print("\nMOST POPULATED GRID CELLS")
    print("=" * 45)

    rows = connection.execute("""
        SELECT grid_id, COUNT(*) AS component_count
        FROM geographical_component_grid
        WHERE assignment_status = 'assigned'
        GROUP BY grid_id
        ORDER BY component_count DESC
        LIMIT 10
    """).fetchall()

    for grid_id, count in rows:
        print(f"{grid_id}: {count:,}")

finally:
    connection.close()