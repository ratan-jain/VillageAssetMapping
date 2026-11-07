
from math import ceil, floor, isfinite
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box


DEFAULT_CELL_SIZE_METRES = 500
DEFAULT_TARGET_CRS = "EPSG:32643"


def _validate_cell_size(cell_size):
    """
    Validate the requested grid cell size.

    Cell size must be a finite positive number.
    """
    if isinstance(cell_size, bool) or not isinstance(
        cell_size, (int, float)
    ):
        raise ValueError("Cell size must be a number.")

    if not isfinite(cell_size) or cell_size <= 0:
        raise ValueError("Cell size must be a positive finite number.")


def _load_boundary(boundary_source):
    """
    Load and validate the study-area boundary.

    Accepts either a file path or a GeoDataFrame.
    """
    if isinstance(boundary_source, gpd.GeoDataFrame):
        boundary = boundary_source.copy()

    else:
        boundary_path = Path(boundary_source)

        if not boundary_path.is_file():
            raise FileNotFoundError(
                f"Boundary file not found: {boundary_path}"
            )

        boundary = gpd.read_file(boundary_path)

    if boundary.empty:
        raise ValueError("Boundary dataset is empty.")

    if boundary.crs is None:
        raise ValueError("Boundary dataset must have a defined CRS.")

    if boundary.geometry.isna().any():
        raise ValueError("Boundary contains missing geometries.")

    if boundary.geometry.is_empty.any():
        raise ValueError("Boundary contains empty geometries.")

    if not boundary.geometry.is_valid.all():
        raise ValueError("Boundary contains invalid geometries.")

    allowed_types = {"Polygon", "MultiPolygon"}

    if not boundary.geometry.geom_type.isin(allowed_types).all():
        raise ValueError(
            "Boundary must contain Polygon or MultiPolygon geometries."
        )

    return boundary


def generate_grid(
    boundary_source,
    cell_size=DEFAULT_CELL_SIZE_METRES,
    target_crs=DEFAULT_TARGET_CRS,
):
    """
    Generate a regular square fishnet clipped to a study-area boundary.

    Grid cells are aligned to a fixed projected coordinate origin (0, 0).

    Args:
        boundary_source:
            GeoDataFrame or path to a geographic boundary file.

        cell_size:
            Square cell width and height in metres.

        target_crs:
            Projected coordinate reference system.

    Returns:
        GeoDataFrame containing clipped grid cells.

    Raises:
        ValueError: If the boundary or cell size is invalid.
        FileNotFoundError: If the boundary file does not exist.
    """
    _validate_cell_size(cell_size)

    boundary = _load_boundary(boundary_source)

    # Convert geographic coordinates into projected metres.
    projected_boundary = boundary.to_crs(target_crs)

    # Combine all boundary features into one study-area geometry.
    study_area = projected_boundary.geometry.union_all()

    if study_area.is_empty or study_area.area <= 0:
        raise ValueError("Study-area boundary has no positive area.")

    min_x, min_y, max_x, max_y = study_area.bounds

    # Calculate grid indices using a fixed origin at (0, 0).
    min_column = floor(min_x / cell_size)
    max_column = ceil(max_x / cell_size) - 1

    min_row = floor(min_y / cell_size)
    max_row = ceil(max_y / cell_size) - 1

    full_cell_area = cell_size * cell_size

    grid_records = []

    # Generate cells and clip them against the study-area boundary.
    for row in range(min_row, max_row + 1):

        for column in range(min_column, max_column + 1):

            cell_min_x = column * cell_size
            cell_min_y = row * cell_size

            cell = box(
                cell_min_x,
                cell_min_y,
                cell_min_x + cell_size,
                cell_min_y + cell_size,
            )

            if not cell.intersects(study_area):
                continue

            clipped_cell = cell.intersection(study_area)

            # Ignore cells that only touch the boundary.
            if clipped_cell.is_empty or clipped_cell.area <= 0:
                continue

            clipped_area = clipped_cell.area

            coverage_fraction = clipped_area / full_cell_area

            grid_records.append({
                "Grid_ID": f"GRID-R{row:05d}-C{column:05d}",
                "Row": row,
                "Column": column,
                "Cell_Area_Sqm": full_cell_area,
                "Clipped_Area_Sqm": clipped_area,
                "Coverage_Fraction": min(
                    1.0, coverage_fraction
                ),
                "geometry": clipped_cell,
            })

    if not grid_records:
        raise ValueError("No grid cells intersect the study area.")

    grid = gpd.GeoDataFrame(
        grid_records,
        geometry="geometry",
        crs=target_crs,
    )

    return grid
