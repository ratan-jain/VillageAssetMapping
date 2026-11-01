
from AssetDatabase import AssetDatabase
from DataValidator import validate_asset, SUPPORTED_CATEGORIES


class AssetManager:
    def __init__(self, database_path="VillageAssets.db"):
        self.database = AssetDatabase(database_path)

    def add_asset(
        self,
        name,
        village,
        category,
        latitude,
        longitude,
        owner_type,
        owner_name,
        managing_authority=None,
        verification_status="unverified",
    ):
        existing_assets = self.database.list_assets()
        next_number = 1

        for asset in existing_assets:
            asset_number = int(asset["id"].split("-")[1])
            next_number = max(next_number, asset_number + 1)

        asset_id = f"AST-{next_number:06d}"

        asset = {
            "id": asset_id,
            "name": name,
            "village": village,
            "category": category,
            "latitude": latitude,
            "longitude": longitude,
            "owner_type": owner_type,
            "owner_name": owner_name,
            "managing_authority": managing_authority,
            "verification_status": verification_status,
        }

        errors = validate_asset(asset)

        if errors:
            return {"success": False, "errors": errors}

        self.database.save_asset(asset)

        return {"success": True, "asset": asset.copy()}

    def get_asset(self, asset_id):
        return self.database.get_asset(asset_id)

    def list_assets(self):
        return self.database.list_assets()

    def update_owner_name(self, asset_id, new_owner_name):
        if not isinstance(new_owner_name, str) or not new_owner_name.strip():
            return {
                "success": False,
                "errors": ["Owner name must be non-empty text."],
            }

        success = self.database.update_asset(
            asset_id,
            {"owner_name": new_owner_name.strip()},
        )

        if not success:
            return {"success": False, "errors": ["Asset not found."]}

        return {"success": True, "asset": self.get_asset(asset_id)}

    def search_assets(self, query):
        if not isinstance(query, str) or not query.strip():
            return []

        query = query.strip().casefold()

        return [
            asset
            for asset in self.list_assets()
            if query in asset["name"].casefold()
            or query in asset["village"].casefold()
            or query in asset["owner_name"].casefold()
        ]

    def filter_by_category(self, category):
        if (
            not isinstance(category, str)
            or category not in SUPPORTED_CATEGORIES
        ):
            return []

        return [
            asset
            for asset in self.list_assets()
            if asset["category"] == category
        ]

    def close(self):
        self.database.close()
