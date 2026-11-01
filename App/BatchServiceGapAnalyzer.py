
from ServiceGapAnalyzer import ServiceGapAnalyzer


class BatchServiceGapAnalyzer:
    def __init__(self, asset_manager):
        self.analyzer = ServiceGapAnalyzer(asset_manager)

    def analyze_villages(self, villages, category, maximum_distance_km):
        results = []

        for village in villages:
            result = self.analyzer.analyze_village(
                village_name=village["name"],
                village_latitude=village["latitude"],
                village_longitude=village["longitude"],
                category=category,
                maximum_distance_km=maximum_distance_km,
            )

            results.append(result)

        return results
