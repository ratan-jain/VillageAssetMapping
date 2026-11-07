import sqlite3
from pathlib import Path

import geopandas as gpd
import pandas as pd


DEFAULT_BATCH_SIZE = 25_000
SOURCE_CRS = "EPSG:4326"
ASSIGNMENT_METHOD = "representative_point_intersects"


def _validate_inputs(grid, batch_size):
    """Validate the grid and processing configuration."""

    if not isinstance(grid, gpd.GeoDataFrame):
        raise TypeError("grid must be a GeoDataFrame.")

    if grid.empty:
        raise ValueError("Grid cannot be empty.")

    if grid.crs is None:
        raise ValueError("Grid must have a defined CRS.")

    if "Grid_ID" not in grid.columns:
        raise ValueError("Grid must contain a Grid_ID column.")

    if grid["Grid_ID"].isna().any():
        raise ValueError("Grid_ID cannot contain null values.")

    if grid["Grid_ID"].duplicated().any():
        raise ValueError("Grid_ID values must be unique.")

    if grid.geometry.isna().any() or grid.geometry.is_empty.any():
        raise ValueError("Grid cannot contain empty geometries.")

    if not grid.geometry.is_valid.all():
        raise ValueError("Grid contains invalid geometries.")

    if (
        isinstance(batch_size, bool)
        or not isinstance(batch_size, int)
        or batch_size <= 0
    ):
        raise ValueError("batch_size must be a positive integer.")


def _create_assignment_table(connection):
    """Create the separate component-to-grid mapping table."""

    connection.execute("""
        CREATE TABLE IF NOT EXISTS geographical_component_grid (
            component_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL UNIQUE,
            grid_id TEXT,
            assignment_status TEXT NOT NULL,
            assignment_method TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_component_grid_grid_id
        ON geographical_component_grid(grid_id)
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_component_grid_status
        ON geographical_component_grid(assignment_status)
    """)

    connection.commit()


def _assign_batch(batch, grid):
    """Assign one batch of OSM representative points to grid cells."""

    points = gpd.GeoDataFrame(
        batch,
        geometry=gpd.points_from_xy(
            batch["longitude"],
            batch["latitude"]
        ),
        crs=SOURCE_CRS
    )

    points = points.to_crs(grid.crs)

    joined = gpd.sjoin(
        points,
        grid[["Grid_ID", "geometry"]],
        how="left",
        predicate="intersects"
    )

    # A point on a shared cell boundary may intersect multiple cells.
    # Resolve this deterministically by selecting the smallest Grid_ID.
    joined = joined.sort_values(
        ["id", "Grid_ID"],
        na_position="last"
    )

    duplicate_matches = len(joined) - joined["id"].nunique()

    assignments = joined.drop_duplicates(
        subset="id",
        keep="first"
    )

    records = []

    for row in assignments.itertuples(index=False):
        grid_id = row.Grid_ID

        status = (
            "assigned"
            if pd.notna(grid_id)
            else "outside_grid"
        )

        records.append((
            row.id,
            row.source_id,
            grid_id if pd.notna(grid_id) else None,
            status,
            ASSIGNMENT_METHOD
        ))

    return records, duplicate_matches


def assign_components_to_grid(
    database_path,
    grid,
    batch_size=DEFAULT_BATCH_SIZE
):
    """
    Assign geographical_components to grid cells in batches.

    The original geographical_components table is never modified.

    Returns a summary dictionary containing assignment statistics.
    """

    _validate_inputs(grid, batch_size)

    database_path = Path(database_path)

    if not database_path.is_file():
        raise FileNotFoundError(
            f"Database not found: {database_path}"
        )

    connection = sqlite3.connect(database_path)

    try:
        _create_assignment_table(connection)

        # Replace previous assignments atomically.
        connection.execute("BEGIN IMMEDIATE")

        connection.execute(
            "DELETE FROM geographical_component_grid"
        )

        cursor = connection.execute("""
            SELECT
                id,
                source_id,
                latitude,
                longitude
            FROM geographical_components
            ORDER BY id
        """)

        total = 0
        assigned = 0
        unmatched = 0
        boundary_duplicates = 0

        insert_query = """
            INSERT INTO geographical_component_grid (
                component_id,
                source_id,
                grid_id,
                assignment_status,
                assignment_method
            )
            VALUES (?, ?, ?, ?, ?)
        """

        while True:
            rows = cursor.fetchmany(batch_size)

            if not rows:
                break

            columns = [
                "id",
                "source_id",
                "latitude",
                "longitude"
            ]

            batch = pd.DataFrame.from_records(
                rows,
                columns=columns
            )

            records, duplicate_matches = _assign_batch(
                batch,
                grid
            )

            connection.executemany(
                insert_query,
                records
            )

            batch_assigned = sum(
                record[3] == "assigned"
                for record in records
            )

            total += len(records)
            assigned += batch_assigned
            unmatched += len(records) - batch_assigned
            boundary_duplicates += duplicate_matches

            print(
                f"Processed: {total:,} | "
                f"Assigned: {assigned:,} | "
                f"Outside grid: {unmatched:,}"
            )

        connection.commit()

        return {
            "total_processed": total,
            "assigned": assigned,
            "outside_grid": unmatched,
            "boundary_duplicate_matches": boundary_duplicates,
            "grid_cells": len(grid),
            "batch_size": batch_size
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()