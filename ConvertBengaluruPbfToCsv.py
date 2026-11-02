#!/usr/bin/env python3
"""
Convert a downloaded OpenStreetMap .osm.pbf extract into the
Village Asset Mapping CSV schema.

Requirements:
    python -m pip install osmium

Usage (from the project folder):
    python ConvertBengaluruPbfToCsv.py

Optional:
    python ConvertBengaluruPbfToCsv.py "planet_77.115,12.648_78.078,13.355.osm.pbf"
    python ConvertBengaluruPbfToCsv.py input.osm.pbf --out BengaluruComponents.csv

Important:
- This exports tagged OSM nodes and ways with useful map-feature tags.
- Way coordinates are represented by the average of their available vertices,
  not by their full geometry.
- Relations are not exported by this first converter.
- The supplied extract's bounding box is larger than Bengaluru Urban district.
  Do not treat this CSV as exact district-only data until it is clipped using
  an authoritative district boundary.
- All rows are marked "unverified".
"""

import argparse
import csv
import sys
from pathlib import Path

try:
    import osmium
except ImportError:
    print("Missing dependency. Install it with: python -m pip install osmium")
    raise SystemExit(1)

FIELDS = [
    "id", "name", "village", "category", "latitude", "longitude",
    "owner_type", "owner_name", "managing_authority", "verification_status",
    "source", "source_id", "source_url", "osm_type", "component_type",
    "tags_json", "geometry_method"
]

# Keep objects that have at least one of these useful map-feature tags.
FEATURE_KEYS = {
    "name", "amenity", "building", "highway", "waterway", "natural",
    "landuse", "leisure", "shop", "tourism", "railway",
    "public_transport", "man_made", "healthcare", "office",
    "aeroway", "barrier", "power", "historic", "sport",
    "public_service", "craft", "emergency", "military",
    "boundary", "place", "water", "surface"
}

def classify(t):
    amenity = t.get("amenity", "")
    healthcare = t.get("healthcare", "")
    building = t.get("building", "")
    highway = t.get("highway", "")
    natural = t.get("natural", "")
    waterway = t.get("waterway", "")
    landuse = t.get("landuse", "")
    leisure = t.get("leisure", "")
    railway = t.get("railway", "")
    pt = t.get("public_transport", "")

    if amenity in {"school", "kindergarten"} or building == "school":
        return "school"
    if amenity in {"university", "college"} or building == "university":
        return "college"
    if amenity in {"hospital", "clinic", "doctors", "dentist"} or healthcare:
        return "hospital"
    if amenity in {"bus_station", "bus_stop"} or pt in {"platform", "stop_position"}:
        return "transport"
    if railway:
        return "railway"
    if highway:
        return "road"
    if waterway or natural in {"water", "wetland", "bay"} or landuse in {"reservoir", "basin"} or t.get("water"):
        return "water"
    if natural in {"wood", "scrub"} or landuse == "forest":
        return "forest"
    if leisure in {"park", "playground", "garden", "sports_centre", "pitch", "nature_reserve"}:
        return "park"
    if amenity in {"police", "fire_station", "post_office", "library", "community_centre",
                   "townhall", "courthouse", "toilets", "drinking_water", "waste_disposal"}:
        return "public_facility"
    if building:
        return "building"
    if amenity:
        return "public_facility"
    if t.get("shop"):
        return "commercial"
    if t.get("tourism"):
        return "tourism"
    if t.get("man_made") or t.get("power"):
        return "infrastructure"
    if landuse:
        return "land_use"
    if t.get("place"):
        return "settlement"
    return "other"

def tags_to_dict(tags):
    return {tag.k: tag.v for tag in tags}

def first_component_tag(tags):
    preferred = (
        "building", "highway", "amenity", "healthcare", "natural",
        "waterway", "leisure", "landuse", "man_made", "railway",
        "public_transport", "shop", "tourism", "power", "place"
    )
    for key in preferred:
        if tags.get(key):
            return tags[key]
    return "other"

def has_feature_tag(tags):
    return any(k in FEATURE_KEYS for k in tags)

class CsvWriter(osmium.SimpleHandler):
    def __init__(self, writer):
        super().__init__()
        self.writer = writer
        self.node_count = 0
        self.way_count = 0
        self.skipped = 0
        self.category_counts = {}

    def write_record(self, osm_type, osm_id, tags, lat, lon, method):
        if not has_feature_tag(tags):
            self.skipped += 1
            return
        category = classify(tags)
        source_id = f"{osm_type}/{osm_id}"
        row = {
            "id": f"OSM-{osm_type[0].upper()}-{osm_id}",
            "name": tags.get("name") or tags.get("official_name") or tags.get("brand") or "",
            "village": tags.get("addr:suburb") or tags.get("addr:hamlet") or tags.get("addr:village") or "",
            "category": category,
            "latitude": f"{lat:.7f}",
            "longitude": f"{lon:.7f}",
            "owner_type": tags.get("ownership", ""),
            "owner_name": tags.get("operator", ""),
            "managing_authority": tags.get("operator", ""),
            "verification_status": "unverified",
            "source": "OpenStreetMap",
            "source_id": source_id,
            "source_url": f"https://www.openstreetmap.org/{source_id}",
            "osm_type": osm_type,
            "component_type": first_component_tag(tags),
            "tags_json": __import__("json").dumps(tags, ensure_ascii=False, sort_keys=True),
            "geometry_method": method,
        }
        self.writer.writerow(row)
        self.category_counts[category] = self.category_counts.get(category, 0) + 1

    def node(self, n):
        if not n.location.valid():
            self.skipped += 1
            return
        tags = tags_to_dict(n.tags)
        self.write_record("node", n.id, tags, n.location.lat, n.location.lon, "node")
        self.node_count += 1

    def way(self, w):
        tags = tags_to_dict(w.tags)
        if not has_feature_tag(tags):
            self.skipped += 1
            return
        lats, lons = [], []
        try:
            for nd in w.nodes:
                loc = nd.location
                if loc.valid():
                    lats.append(loc.lat)
                    lons.append(loc.lon)
        except Exception:
            pass
        if not lats:
            self.skipped += 1
            return
        lat = sum(lats) / len(lats)
        lon = sum(lons) / len(lons)
        self.write_record("way", w.id, tags, lat, lon, "average_of_way_vertices")
        self.way_count += 1

def main():
    parser = argparse.ArgumentParser(description="Convert OSM PBF into Village Asset Mapping CSV.")
    parser.add_argument("pbf", nargs="?", help="Path to .osm.pbf file")
    parser.add_argument("--out", default="BengaluruComponents.csv", help="Output CSV filename")
    args = parser.parse_args()

    if args.pbf:
        pbf = Path(args.pbf)
    else:
        candidates = sorted(Path.cwd().glob("*.osm.pbf"))
        if len(candidates) == 1:
            pbf = candidates[0]
        elif not candidates:
            print("No .osm.pbf file found in this folder.")
            print("Pass the full path to the PBF file as the first argument.")
            return 2
        else:
            print("More than one .osm.pbf file found. Specify which one to convert:")
            for f in candidates:
                print(f"  {f.name}")
            return 2

    if not pbf.is_file():
        print(f"PBF file not found: {pbf}")
        return 2

    out_path = Path(args.out)
    print(f"Input:  {pbf.resolve()}")
    print(f"Output: {out_path.resolve()}")
    print("Reading PBF. This may take a few minutes...")

    try:
        with out_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=FIELDS)
            writer.writeheader()
            handler = CsvWriter(writer)
            handler.apply_file(str(pbf), locations=True, idx="flex_mem")
    except Exception as exc:
        print(f"\nConversion failed: {type(exc).__name__}: {exc}")
        print("The source PBF has not been modified.")
        return 1

    total = sum(handler.category_counts.values())
    print("\nConversion complete.")
    print(f"Nodes processed: {handler.node_count:,}")
    print(f"Ways processed: {handler.way_count:,}")
    print(f"Rows written: {total:,}")
    print(f"Skipped objects: {handler.skipped:,}")
    print("\nCategory counts:")
    for category, count in sorted(handler.category_counts.items()):
        print(f"  {category:20s} {count:>9,}")
    print(f"\nCSV created: {out_path.resolve()}")

    if total < 10000:
        print("\nNOTE: The extract produced fewer than 10,000 qualifying rows.")
        print("Do not create synthetic records to reach the target.")
    print("\nIMPORTANT: This is the extract's bounding-box coverage, not yet exact")
    print("Bengaluru Urban district clipping. All rows are marked unverified.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
