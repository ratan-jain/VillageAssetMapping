#!/usr/bin/env python3
"""Filter BengaluruComponents.csv to a GeoJSON Polygon/MultiPolygon boundary.
Standard-library only. Keeps rows whose representative point is inside.
This does not clip full road/building geometries; way points in the source CSV
are averages of vertices. The source CSV is never modified.
"""
import argparse
import csv
import json
import math
from pathlib import Path

def on_segment(px, py, ax, ay, bx, by, eps=1e-10):
    cross = (px-ax)*(by-ay) - (py-ay)*(bx-ax)
    if abs(cross) > eps:
        return False
    return (px-ax)*(px-bx) + (py-ay)*(py-by) <= eps

def in_ring(x, y, ring):
    if len(ring) < 3:
        return False
    inside = False
    j = len(ring)-1
    for i in range(len(ring)):
        ax, ay = ring[j][0], ring[j][1]
        bx, by = ring[i][0], ring[i][1]
        if on_segment(x, y, ax, ay, bx, by):
            return True
        if (ay > y) != (by > y):
            cross_x = (bx-ax)*(y-ay)/(by-ay) + ax
            if x < cross_x:
                inside = not inside
        j = i
    return inside

def in_polygon(x, y, rings):
    return bool(rings) and in_ring(x, y, rings[0]) and not any(
        in_ring(x, y, hole) for hole in rings[1:]
    )

def read_polygons(path):
    with Path(path).open(encoding="utf-8") as f:
        data = json.load(f)
    if data.get("type") == "FeatureCollection":
        features = data.get("features", [])
    elif data.get("type") == "Feature":
        features = [data]
    else:
        raise ValueError("Expected GeoJSON FeatureCollection or Feature.")
    polygons = []
    for feature in features:
        geom = (feature or {}).get("geometry") or {}
        typ, coords = geom.get("type"), geom.get("coordinates") or []
        if typ == "Polygon":
            polygons.append(coords)
        elif typ == "MultiPolygon":
            polygons.extend(coords)
        elif typ:
            raise ValueError(f"Unsupported geometry: {typ}")
    if not polygons:
        raise ValueError("No Polygon/MultiPolygon geometry found.")
    return polygons, len(features)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="BengaluruComponents.csv")
    ap.add_argument("--boundary", default="BengaluruUrbanBoundary.geojson")
    ap.add_argument("--output", default="BengaluruUrbanComponents.csv")
    args = ap.parse_args()
    src_path, boundary_path, out_path = map(Path, (args.input, args.boundary, args.output))
    for p in (src_path, boundary_path):
        if not p.is_file():
            print(f"ERROR: file not found: {p.resolve()}")
            return 2

    polygons, feature_count = read_polygons(boundary_path)
    print(f"Boundary features: {feature_count}; polygon parts: {len(polygons)}")
    print(f"Reading: {src_path.resolve()}")
    print(f"Writing: {out_path.resolve()}")
    print("Filtering by representative latitude/longitude...")

    total = kept = outside = invalid = duplicates = 0
    categories = {}
    seen = set()
    with src_path.open(encoding="utf-8-sig", newline="") as src, \
         out_path.open("w", encoding="utf-8-sig", newline="") as dst:
        reader = csv.DictReader(src)
        if not reader.fieldnames or not {"latitude", "longitude"}.issubset(reader.fieldnames):
            raise ValueError("CSV must contain latitude and longitude.")
        writer = csv.DictWriter(dst, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            total += 1
            try:
                lat, lon = float(row["latitude"]), float(row["longitude"])
                if not (math.isfinite(lat) and math.isfinite(lon)
                        and -90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError()
            except (TypeError, ValueError):
                invalid += 1
                continue
            if not any(in_polygon(lon, lat, poly) for poly in polygons):
                outside += 1
                continue
            sid = row.get("source_id", "")
            if sid:
                if sid in seen:
                    duplicates += 1
                    continue
                seen.add(sid)
            writer.writerow(row)
            kept += 1
            cat = row.get("category") or "(blank)"
            categories[cat] = categories.get(cat, 0) + 1
            if total % 100000 == 0:
                print(f"Processed {total:,}; kept {kept:,}...")

    print("\nSPATIAL FILTER COMPLETE")
    print(f"Input rows: {total:,}")
    print(f"Rows inside boundary: {kept:,}")
    print(f"Rows outside boundary: {outside:,}")
    print(f"Invalid coordinates: {invalid:,}")
    print(f"Duplicate source IDs skipped: {duplicates:,}")
    print("\nCategory counts:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat:20s} {count:>10,}")
    print(f"\nCreated: {out_path.resolve()}")
    print("NOTE: representative-point filter only; full feature geometry is not clipped.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
