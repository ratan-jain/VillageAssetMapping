
from App.FacilityClassificationManager import classify_all_components


DATABASE_PATH = "VillageAssets.db"
BATCH_SIZE = 25_000

print("Starting Bengaluru Urban facility classification...")

result = classify_all_components(
    database_path=DATABASE_PATH,
    batch_size=BATCH_SIZE
)

print("\nFACILITY CLASSIFICATION SUMMARY")
print("=" * 45)

print(f"Total processed: {result['total_processed']:,}")
print(f"Classified: {result['classified']:,}")
print(f"Needs review: {result['needs_review']:,}")

print("\nSERVICE GROUP DISTRIBUTION")
print("=" * 45)

for group, count in result["service_group_counts"].items():
    print(f"{group}: {count:,}")

print("\nClassification completed.")
