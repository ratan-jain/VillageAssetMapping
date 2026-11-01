import math

from AssetManager import AssetManager
from DistanceCalculator import calculate_distance_km


class NearbyAssetFinder:
    def __init__(self, asset_manager):
        self.asset_manager = asset_manager

    def find_nearby_assets(self, latitude, longitude, radius_km, category=None):
        if isinstance(radius_km, bool) or not isinstance(radius_km, (int, float)):
            raise ValueError("Radius must be a number.")

        if radius_km < 0 or not math.isfinite(radius_km):
            raise ValueError("Radius must be a finite, non-negative number.")

        nearby_assets = []

        for asset in self.asset_manager.list_assets():
            if category is not None and asset["category"] != category:
                continue

            distance = calculate_distance_km(
                latitude,
                longitude,
                asset["latitude"],
                asset["longitude"],
            )

            if distance <= radius_km:
                result = asset.copy()
                result["distance_km"] = round(distance, 3)
                nearby_assets.append(result)

        nearby_assets.sort(key=lambda asset: asset["distance_km"])
        return nearby_assets
