import geopandas as gpd

from App.AssetGridAssigner import assign_components_to_grid
from App.GridGenerator import generate_grid


BOUNDARY_PATH = "BengaluruUrbanBoundary.geojson"
DATABASE_PATH = "VillageAssets.db"


print("Generating Bengaluru Urban grid...")

grid = generate_grid(BOUNDARY_PATH)

print(f"Grid cells generated: {len(grid):,}")
print(f"Grid CRS: {grid.crs}")

print("\nStarting OSM component assignment...")

result = assign_components_to_grid(
    database_path=DATABASE_PATH,
    grid=grid,
    batch_size=25_000
)

print("\nASSIGNMENT SUMMARY")
print("------------------")

for key, value in result.items():
    print(f"{key}: {value:,}" if isinstance(value, int) else f"{key}: {value}")