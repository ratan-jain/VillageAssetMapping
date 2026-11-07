
from App.GridGenerator import generate_grid
from App.GridServiceAnalyzer import analyze_grid_services


BOUNDARY_PATH = "BengaluruUrbanBoundary.geojson"
DATABASE_PATH = "VillageAssets.db"

OUTPUT_CSV = "BengaluruGridServiceAnalysis.csv"
OUTPUT_GEOJSON = "BengaluruGridServiceAnalysis.geojson"


print("\nGENERATING BENGALURU URBAN GRID")
print("=" * 45)

grid = generate_grid(BOUNDARY_PATH)

print(f"Grid cells: {len(grid):,}")
print(f"CRS: {grid.crs}")


print("\nANALYZING GRID-LEVEL SERVICES")
print("=" * 45)

result = analyze_grid_services(
    database_path=DATABASE_PATH,
    grid=grid
)

grid_results = result["grid_results"]
summary = result["summary"]


print("\nSERVICE GAP ANALYSIS SUMMARY")
print("=" * 45)

for key, value in summary.items():
    print(f"{key}: {value:,}")


print("\nEXPORTING RESULTS")
print("=" * 45)

grid_results.to_csv(
    OUTPUT_CSV,
    index=False
)

grid_results.to_crs("EPSG:4326").to_file(
    OUTPUT_GEOJSON,
    driver="GeoJSON"
)

print(f"CSV: {OUTPUT_CSV}")
print(f"GeoJSON: {OUTPUT_GEOJSON}")

print("\nGRID SERVICE ANALYSIS COMPLETED!")
