import math

from AssetManager import AssetManager
from DistanceCalculator import calculate_distance_km


class ServiceGapAnalyzer:
    def __init__(self, asset_manager):
        self.asset_manager = asset_manager

    def analyze_village(
        self,
        village_name,
        village_latitude,
        village_longitude,
        category,
        maximum_distance_km,
    ):
        if not isinstance(village_name, str) or not village_name.strip():
            raise ValueError("Village name must be non-empty text.")

        if (
            isinstance(maximum_distance_km, bool)
            or not isinstance(maximum_distance_km, (int, float))
            or not math.isfinite(maximum_distance_km)
            or maximum_distance_km < 0
        ):
            raise ValueError(
                "Maximum distance must be a finite, non-negative number."
            )

        assets = self.asset_manager.filter_by_category(category)

        nearest_asset = None
        nearest_distance = None

        for asset in assets:
            distance = calculate_distance_km(
                village_latitude,
                village_longitude,
                asset["latitude"],
                asset["longitude"],
            )

            if nearest_distance is None or distance < nearest_distance:
                nearest_distance = distance
                nearest_asset = asset

        if nearest_asset is None:
            return {
                "village": village_name.strip(),
                "category": category,
                "status": "no_facility_found",
                "nearest_asset": None,
                "distance_km": None,
                "maximum_distance_km": maximum_distance_km,
            }

        status = (
            "within_range"
            if nearest_distance <= maximum_distance_km
            else "potential_service_gap"
        )

        return {
            "village": village_name.strip(),
            "category": category,
            "status": status,
            "nearest_asset": nearest_asset,
            "distance_km": round(nearest_distance, 3),
            "maximum_distance_km": maximum_distance_km,
        }
