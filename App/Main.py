
from pathlib import Path

from AssetManager import AssetManager
from NearbyAssetFinder import NearbyAssetFinder
from ServiceGapAnalyzer import ServiceGapAnalyzer
from BatchServiceGapAnalyzer import BatchServiceGapAnalyzer
from AssetCsvManager import AssetCsvManager


# --------------------------------------------------
# INPUT HELPERS
# --------------------------------------------------

def read_float(prompt):
    """Read a valid floating-point number from the user."""
    while True:
        try:
            return float(input(prompt).strip())
        except ValueError:
            print("Invalid input. Please enter a valid number.")


def read_integer(prompt, minimum=1):
    """Read an integer greater than or equal to minimum."""
    while True:
        try:
            value = int(input(prompt).strip())

            if value < minimum:
                print(f"Enter a number greater than or equal to {minimum}.")
                continue

            return value

        except ValueError:
            print("Invalid input. Please enter a whole number.")


def read_non_empty(prompt):
    """Read text that cannot be empty."""
    while True:
        value = input(prompt).strip()

        if value:
            return value

        print("This field cannot be empty.")


# --------------------------------------------------
# DISPLAY FUNCTIONS
# --------------------------------------------------

def display_menu():
    print("\n" + "=" * 44)
    print("          VILLAGE ASSET MAPPING")
    print("=" * 44)
    print("1. Add a new asset")
    print("2. View all assets")
    print("3. Search assets")
    print("4. Find nearby facilities")
    print("5. Analyze village service gaps")
    print("6. Import assets from CSV")
    print("7. Export assets to CSV")
    print("8. Exit")
    print("=" * 44)


def display_asset(asset):
    """Display an individual asset."""
    print("\n--------------------------------------------")
    print("Asset ID:", asset["id"])
    print("Name:", asset["name"])
    print("Village:", asset["village"])
    print("Category:", asset["category"])
    print("Latitude:", asset["latitude"])
    print("Longitude:", asset["longitude"])
    print("Owner Type:", asset["owner_type"])
    print("Owner Name:", asset["owner_name"])
    print("Managing Authority:", asset["managing_authority"])
    print("Verification Status:", asset["verification_status"])

    if "distance_km" in asset:
        print("Distance:", asset["distance_km"], "km")

    print("--------------------------------------------")


def display_assets(assets):
    """Display a collection of assets."""
    if not assets:
        print("\nNo assets found.")
        return

    print(f"\nTotal assets found: {len(assets)}")

    for asset in assets:
        display_asset(asset)


# --------------------------------------------------
# ASSET MANAGEMENT
# --------------------------------------------------

def add_new_asset(asset_manager):
    print("\n========== ADD NEW ASSET ==========")

    name = read_non_empty("Enter asset name: ")
    village = read_non_empty("Enter village name: ")
    category = read_non_empty("Enter category: ").lower()

    latitude = read_float("Enter latitude: ")
    longitude = read_float("Enter longitude: ")

    owner_type = read_non_empty("Enter owner type: ").lower()
    owner_name = read_non_empty("Enter owner name: ")

    managing_authority = input(
        "Enter managing authority (optional): "
    ).strip() or None

    result = asset_manager.add_asset(
        name=name,
        village=village,
        category=category,
        latitude=latitude,
        longitude=longitude,
        owner_type=owner_type,
        owner_name=owner_name,
        managing_authority=managing_authority,
    )

    if result["success"]:
        print("\nAsset added successfully!")
        print("Generated Asset ID:", result["asset"]["id"])
    else:
        print("\nAsset could not be added.")

        for error in result["errors"]:
            print("-", error)


def view_all_assets(asset_manager):
    print("\n========== ALL ASSETS ==========")

    assets = asset_manager.list_assets()
    display_assets(assets)


def search_assets(asset_manager):
    print("\n========== SEARCH ASSETS ==========")

    query = read_non_empty(
        "Enter asset name, village or owner name: "
    )

    results = asset_manager.search_assets(query)
    display_assets(results)


# --------------------------------------------------
# GEOGRAPHIC ANALYSIS
# --------------------------------------------------

def find_nearby_facilities(nearby_finder):
    print("\n========== FIND NEARBY FACILITIES ==========")

    latitude = read_float("Enter your latitude: ")
    longitude = read_float("Enter your longitude: ")
    radius = read_float("Enter search radius in kilometres: ")

    category = input(
        "Enter category (leave blank for all categories): "
    ).strip().lower() or None

    try:
        results = nearby_finder.find_nearby_assets(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius,
            category=category,
        )

        display_assets(results)

    except ValueError as error:
        print("Invalid geographic input:", error)


def analyze_single_village(service_analyzer):
    print("\n========== SERVICE GAP ANALYSIS ==========")

    village_name = read_non_empty("Enter village name: ")
    latitude = read_float("Enter village latitude: ")
    longitude = read_float("Enter village longitude: ")

    category = read_non_empty(
        "Enter facility category to analyze: "
    ).lower()

    maximum_distance = read_float(
        "Enter maximum acceptable distance (km): "
    )

    try:
        result = service_analyzer.analyze_village(
            village_name=village_name,
            village_latitude=latitude,
            village_longitude=longitude,
            category=category,
            maximum_distance_km=maximum_distance,
        )

        print("\n========== ANALYSIS RESULT ==========")
        print("Village:", result["village"])
        print("Category:", result["category"])
        print("Status:", result["status"])

        if result["nearest_asset"] is not None:
            print("Nearest facility:")
            display_asset(result["nearest_asset"])
            print("Distance:", result["distance_km"], "km")
        else:
            print("No matching facility was found.")

    except ValueError as error:
        print("Analysis error:", error)


def analyze_multiple_villages(batch_analyzer):
    print("\n========== BATCH SERVICE GAP ANALYSIS ==========")

    village_count = read_integer("How many villages? ")

    villages = []

    for index in range(village_count):
        print(f"\nEnter details for village {index + 1}")

        village = {
            "name": read_non_empty("Village name: "),
            "latitude": read_float("Latitude: "),
            "longitude": read_float("Longitude: "),
        }

        villages.append(village)

    category = read_non_empty(
        "Enter facility category: "
    ).lower()

    maximum_distance = read_float(
        "Enter maximum acceptable distance (km): "
    )

    try:
        results = batch_analyzer.analyze_villages(
            villages=villages,
            category=category,
            maximum_distance_km=maximum_distance,
        )

        print("\n========== BATCH ANALYSIS REPORT ==========")

        for result in results:
            print("\nVillage:", result["village"])
            print("Category:", result["category"])
            print("Status:", result["status"])
            print("Distance:", result["distance_km"], "km")

    except ValueError as error:
        print("Batch analysis error:", error)


# --------------------------------------------------
# CSV OPERATIONS
# --------------------------------------------------

def import_assets_from_csv(csv_manager):
    print("\n========== IMPORT ASSETS ==========")

    file_path = read_non_empty("Enter CSV file path: ")

    try:
        result = csv_manager.import_assets(file_path)

        print("\nSuccessfully imported:", result["imported"])

        if result["errors"]:
            print("\nImport errors:")

            for error in result["errors"]:
                print("-", error)

    except (OSError, ValueError) as error:
        print("Import failed:", error)


def export_assets_to_csv(csv_manager):
    print("\n========== EXPORT ASSETS ==========")

    file_path = read_non_empty(
        "Enter destination CSV file path: "
    )

    try:
        count = csv_manager.export_assets(file_path)

        print(f"\nSuccessfully exported {count} assets.")
        print("File location:", Path(file_path).resolve())

    except OSError as error:
        print("Export failed:", error)


# --------------------------------------------------
# MAIN APPLICATION
# --------------------------------------------------

def main():
    asset_manager = AssetManager()

    nearby_finder = NearbyAssetFinder(asset_manager)
    service_analyzer = ServiceGapAnalyzer(asset_manager)
    batch_analyzer = BatchServiceGapAnalyzer(asset_manager)
    csv_manager = AssetCsvManager(asset_manager)

    print("\nApplication initialized successfully!")

    try:
        while True:
            display_menu()

            choice = input("Choose an option: ").strip()

            if choice == "1":
                add_new_asset(asset_manager)

            elif choice == "2":
                view_all_assets(asset_manager)

            elif choice == "3":
                search_assets(asset_manager)

            elif choice == "4":
                find_nearby_facilities(nearby_finder)

            elif choice == "5":
                analyze_single_village(service_analyzer)

            elif choice == "6":
                import_assets_from_csv(csv_manager)

            elif choice == "7":
                export_assets_to_csv(csv_manager)

            elif choice == "8":
                print("\nThank you for using Village Asset Mapping!")
                break

            else:
                print("\nInvalid choice. Please select an option from 1 to 8.")

    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user.")

    finally:
        asset_manager.close()
        print("Database connection closed.")


if __name__ == "__main__":
    main()
