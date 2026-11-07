
import sqlite3
from pathlib import Path

from App.FacilityClassifier import classify_component


DEFAULT_BATCH_SIZE = 25_000


def _validate_inputs(database_path, batch_size):
    if not Path(database_path).is_file():
        raise FileNotFoundError(
            f"Database not found: {database_path}"
        )

    if (
        isinstance(batch_size, bool)
        or not isinstance(batch_size, int)
        or batch_size <= 0
    ):
        raise ValueError("batch_size must be a positive integer.")


def _create_classification_table(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS geographical_component_classifications (
            component_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL UNIQUE,
            service_group TEXT NOT NULL,
            service_type TEXT NOT NULL,
            confidence TEXT NOT NULL,
            review_status TEXT NOT NULL,
            classification_reason TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_component_classification_group
        ON geographical_component_classifications(service_group)
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_component_classification_type
        ON geographical_component_classifications(service_type)
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_component_classification_review
        ON geographical_component_classifications(review_status)
    """)

    connection.commit()


def classify_all_components(
    database_path,
    batch_size=DEFAULT_BATCH_SIZE
):
    """
    Classify all geographical components in batches.

    Original geographical data is never modified.

    Previous classification results are replaced atomically.
    """

    _validate_inputs(database_path, batch_size)

    connection = sqlite3.connect(database_path)

    try:
        _create_classification_table(connection)

        connection.execute("BEGIN IMMEDIATE")

        connection.execute("""
            DELETE FROM geographical_component_classifications
        """)

        cursor = connection.execute("""
            SELECT
                id,
                source_id,
                category,
                component_type,
                tags_json,
                name
            FROM geographical_components
            ORDER BY id
        """)

        insert_query = """
            INSERT INTO geographical_component_classifications (
                component_id,
                source_id,
                service_group,
                service_type,
                confidence,
                review_status,
                classification_reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        total = 0
        classified = 0
        needs_review = 0

        while True:
            rows = cursor.fetchmany(batch_size)

            if not rows:
                break

            classification_records = []

            for (
                component_id,
                source_id,
                category,
                component_type,
                tags_json,
                name
            ) in rows:

                result = classify_component(
                    category=category,
                    component_type=component_type,
                    tags_json=tags_json,
                    name=name
                )

                classification_records.append((
                    component_id,
                    source_id,
                    result["service_group"],
                    result["service_type"],
                    result["confidence"],
                    result["review_status"],
                    result["classification_reason"]
                ))

                if result["review_status"] == "classified":
                    classified += 1
                else:
                    needs_review += 1

            connection.executemany(
                insert_query,
                classification_records
            )

            total += len(rows)

            print(
                f"Processed: {total:,} | "
                f"Classified: {classified:,} | "
                f"Needs review: {needs_review:,}"
            )

        connection.commit()

        group_counts = connection.execute("""
            SELECT
                service_group,
                COUNT(*)
            FROM geographical_component_classifications
            GROUP BY service_group
            ORDER BY COUNT(*) DESC
        """).fetchall()

        return {
            "total_processed": total,
            "classified": classified,
            "needs_review": needs_review,
            "batch_size": batch_size,
            "service_group_counts": dict(group_counts)
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
