
import sqlite3

import geopandas as gpd
import pandas as pd


ESSENTIAL_SERVICE_GROUPS = (
    "healthcare",
    "education",
    "emergency",
    "public_service",
    "public_amenity",
    "transport",
    "recreation",
)


def analyze_grid_services(database_path, grid):
    """
    Calculate service distribution for every grid cell.

    Uses:
    - geographical_components
    - geographical_component_grid
    - geographical_component_classifications

    Returns:
    - Grid-level GeoDataFrame
    - Overall analysis summary
    """

    if not database_path:
        raise ValueError("Database path cannot be empty.")

    if not isinstance(grid, gpd.GeoDataFrame):
        raise TypeError("Grid must be a GeoDataFrame.")

    if grid.empty:
        raise ValueError("Grid cannot be empty.")

    if "Grid_ID" not in grid.columns:
        raise ValueError("Grid must contain a Grid_ID column.")

    if grid["Grid_ID"].duplicated().any():
        raise ValueError("Grid contains duplicate Grid_ID values.")

    if grid.crs is None:
        raise ValueError("Grid must have a defined CRS.")

    connection = sqlite3.connect(database_path)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
        """)

        available_tables = {
            row[0] for row in cursor.fetchall()
        }

        required_tables = {
            "geographical_components",
            "geographical_component_grid",
            "geographical_component_classifications",
        }

        missing_tables = required_tables - available_tables

        if missing_tables:
            raise RuntimeError(
                f"Missing database tables: {sorted(missing_tables)}"
            )

        cursor.execute("""
            SELECT
                a.grid_id,
                COUNT(*) AS total_components,

                SUM(
                    CASE
                        WHEN c.review_status = 'classified'
                         AND c.service_group != 'unclassified'
                        THEN 1 ELSE 0
                    END
                ) AS classified_facilities,

                SUM(
                    CASE
                        WHEN c.review_status = 'needs_review'
                        THEN 1 ELSE 0
                    END
                ) AS needs_review

            FROM geographical_component_grid a

            LEFT JOIN geographical_component_classifications c
                ON a.component_id = c.component_id

            GROUP BY a.grid_id
        """)

        component_counts = cursor.fetchall()

        cursor.execute("""
            SELECT
                a.grid_id,
                c.service_group,
                COUNT(*)

            FROM geographical_component_grid a

            JOIN geographical_component_classifications c
                ON a.component_id = c.component_id

            WHERE c.review_status = 'classified'
              AND c.service_group != 'unclassified'

            GROUP BY a.grid_id, c.service_group
        """)

        service_counts = cursor.fetchall()

        cursor.execute("""
            SELECT COUNT(*)
            FROM geographical_components
        """)

        total_source_components = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM geographical_component_grid
        """)

        total_assignments = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM geographical_component_classifications
        """)

        total_classifications = cursor.fetchone()[0]

    finally:
        connection.close()

    # Build lookup dictionaries.

    component_lookup = {
        row[0]: {
            "Total_OSM_Components": row[1] or 0,
            "Classified_Facilities": row[2] or 0,
            "Needs_Review": row[3] or 0,
        }
        for row in component_counts
    }

    service_lookup = {}

    for grid_id, service_group, count in service_counts:
        service_lookup.setdefault(grid_id, {})
        service_lookup[grid_id][service_group] = count

    # Preserve every grid cell, including cells with zero facilities.

    records = []

    for grid_id in grid["Grid_ID"]:
        record = {
            "Grid_ID": grid_id,
            **component_lookup.get(
                grid_id,
                {
                    "Total_OSM_Components": 0,
                    "Classified_Facilities": 0,
                    "Needs_Review": 0,
                },
            ),
        }

        for group in ESSENTIAL_SERVICE_GROUPS:
            record[f"{group}_count"] = (
                service_lookup.get(grid_id, {}).get(group, 0)
            )

        records.append(record)

    results = pd.DataFrame(records)

    grid_results = grid.merge(
        results,
        on="Grid_ID",
        how="left",
        validate="one_to_one",
    )

    # Identify cells without any mapped essential services.

    grid_results["Essential_Service_Total"] = (
        grid_results[
            [f"{group}_count" for group in ESSENTIAL_SERVICE_GROUPS]
        ].sum(axis=1)
    )

    grid_results["Potential_Service_Gap"] = (
        grid_results["Essential_Service_Total"] == 0
    )

    summary = {
        "grid_cells": len(grid_results),
        "source_components": total_source_components,
        "grid_assignments": total_assignments,
        "classification_records": total_classifications,
        "classified_facilities": int(
            grid_results["Classified_Facilities"].sum()
        ),
        "cells_with_mapped_services": int(
            (grid_results["Essential_Service_Total"] > 0).sum()
        ),
        "cells_without_mapped_essential_services": int(
            grid_results["Potential_Service_Gap"].sum()
        ),
    }

    for group in ESSENTIAL_SERVICE_GROUPS:
        summary[f"{group}_total"] = int(
            grid_results[f"{group}_count"].sum()
        )

    return {
        "grid_results": grid_results,
        "summary": summary,
    }
