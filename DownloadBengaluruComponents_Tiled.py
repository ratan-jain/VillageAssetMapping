#!/usr/bin/env python3
"""Resumable tiled OpenStreetMap collector for a Bengaluru-area study.

Downloads real OSM elements from Overpass in small bounding-box tiles, splits
tiles further when requests fail, caches successful results, and writes a CSV.

Without --boundary, the result is an approximate bounding-box extract, NOT an
exact Bengaluru Urban district extract. OSM is community-mapped, not an
official complete inventory. Ways/relations are represented by centre points.
"""
import argparse, csv, json, random, sys, time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
DEFAULT_BBOX = (12.70, 77.35, 13.25, 77.85)  # south, west, north, east
TAG_KEYS = [
    "name", "amenity", "building", "highway", "waterway", "natural",
    "landuse", "leisure", "shop", "tourism", "railway",
    "public_transport", "man_made", "healthcare", "office",
    "aeroway", "barrier",
]
FIELDS = [
    "id", "name", "village", "category", "latitude", "longitude",
    "owner_type", "owner_name", "managing_authority", "verification_status",
    "source", "source_id", "source_url", "osm_type", "component_type",
    "tags_json", "geometry_method", "imported_at"
]

def category_for(t):
    a, h, b = t.get("amenity", ""), t.get("healthcare", ""), t.get("building", "")
    hw, nat, water = t.get("highway", ""), t.get("natural", ""), t.get("waterway", "")
    land, leisure = t.get("landuse", ""), t.get("leisure", "")
    rail, pt = t.get("railway", ""), t.get("public_transport", "")
    if a in {"school", "kindergarten"}: return "school"
    if a in {"university", "college"}: return "college"
    if a in {"hospital", "clinic", "doctors", "dentist", "pharmacy"} or h: return "hospital"
    if a in {"bus_station", "bus_stop"} or pt in {"platform", "stop_position"}: return "transport"
    if a in {"police", "fire_station", "post_office", "library", "community_centre"}: return "public_facility"
    if water or nat in {"water", "wetland", "lake"} or land in {"reservoir", "basin"}: return "water"
    if nat == "wood" or land == "forest": return "forest"
    if leisure in {"park", "playground", "garden", "sports_centre", "pitch"}: return "park"
    if hw: return "road"
    if rail: return "railway"
    if b: return "building"
    if a: return "public_facility"
    if t.get("shop"): return "commercial"
    if t.get("tourism"): return "tourism"
    if t.get("man_made"): return "infrastructure"
    if land: return "land_use"
    return "other"

def point_in_ring(lon, lat, ring):
    inside, j = False, len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and lon < (xj-xi)*(lat-yi)/((yj-yi) or 1e-15)+xi:
            inside = not inside
        j = i
    return inside

def load_boundary(path):
    if not path: return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    polys = []
    for f in data.get("features", []):
        g = f.get("geometry") or {}
        if g.get("type") == "Polygon": polys.append(g["coordinates"])
        elif g.get("type") == "MultiPolygon": polys.extend(g["coordinates"])
    if not polys: raise ValueError("GeoJSON must contain Polygon or MultiPolygon geometry.")
    return polys

def inside(lon, lat, polys):
    if polys is None:
        s,w,n,e = DEFAULT_BBOX
        return w <= lon <= e and s <= lat <= n
    for p in polys:
        if p and point_in_ring(lon, lat, p[0]) and not any(point_in_ring(lon, lat, h) for h in p[1:]):
            return True
    return False

def query_for(b, timeout=90):
    s,w,n,e = b
    keys = "|".join(TAG_KEYS)
    return f'''[out:json][timeout:{timeout}];
(
 node({s},{w},{n},{e})[~"^({keys})$"~"."];
 way({s},{w},{n},{e})[~"^({keys})$"~"."];
 relation({s},{w},{n},{e})[~"^({keys})$"~"."];
);
out center tags;'''

def fetch(query, timeout):
    body = urlencode({"data": query}).encode()
    endpoints = OVERPASS_URLS[:]
    random.shuffle(endpoints)
    errors = []
    for endpoint in endpoints:
        try:
            req = Request(endpoint, data=body, headers={
                "User-Agent": "VillageAssetMapping/1.1 (educational GIS project)",
                "Content-Type": "application/x-www-form-urlencoded"
            }, method="POST")
            with urlopen(req, timeout=timeout) as res:
                return json.loads(res.read().decode("utf-8"))
        except Exception as exc:
            errors.append(f"{endpoint}: {type(exc).__name__}: {exc}")
            time.sleep(2)
    raise RuntimeError(" | ".join(errors))

def split(b):
    s,w,n,e = b
    ml, mn = (s+n)/2, (w+e)/2
    return [(s,w,ml,mn), (s,mn,ml,e), (ml,w,n,mn), (ml,mn,n,e)]

def centre(el):
    if "lat" in el and "lon" in el: return el["lat"], el["lon"], "node"
    c = el.get("center") or {}
    if "lat" in c and "lon" in c: return c["lat"], c["lon"], "center"
    return None

def load_cache(p):
    found = {}
    if p.exists():
        with p.open(encoding="utf-8") as f:
            for line in f:
                try:
                    x = json.loads(line); found[(x["type"], x["id"])] = x
                except (ValueError, KeyError): pass
    return found

def append_cache(p, items):
    with p.open("a", encoding="utf-8") as f:
        for x in items: f.write(json.dumps(x, ensure_ascii=False) + "\\n")

def write_csv(elements, out, boundary):
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rows = []
    for el in elements.values():
        tags = el.get("tags") or {}; pt = centre(el)
        if not pt: continue
        lat, lon, method = pt
        if not inside(lon, lat, boundary): continue
        typ, oid = el.get("type", ""), el.get("id")
        comp = next((tags[k] for k in ("building","highway","amenity","natural","waterway","leisure","landuse","man_made","railway") if tags.get(k)), "other")
        rows.append({
            "id": f"OSM-{typ[0].upper()}-{oid}",
            "name": tags.get("name") or tags.get("official_name") or tags.get("brand") or "",
            "village": tags.get("addr:suburb") or tags.get("addr:hamlet") or tags.get("addr:village") or "",
            "category": category_for(tags), "latitude": f"{lat:.7f}", "longitude": f"{lon:.7f}",
            "owner_type": tags.get("ownership", ""), "owner_name": tags.get("operator", ""),
            "managing_authority": tags.get("operator", ""), "verification_status": "unverified",
            "source": "OpenStreetMap", "source_id": f"{typ}/{oid}",
            "source_url": f"https://www.openstreetmap.org/{typ}/{oid}",
            "osm_type": typ, "component_type": comp,
            "tags_json": json.dumps(tags, ensure_ascii=False, sort_keys=True),
            "geometry_method": method, "imported_at": now
        })
    rows.sort(key=lambda r: (r["category"], r["source_id"]))
    with Path(out).open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    return rows

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="BengaluruComponents.csv")
    p.add_argument("--boundary", help="District boundary GeoJSON for exact filtering")
    p.add_argument("--min-records", type=int, default=10000)
    p.add_argument("--allow-bbox", action="store_true")
    p.add_argument("--tile-size", type=float, default=0.04)
    p.add_argument("--min-tile-size", type=float, default=0.005)
    p.add_argument("--request-timeout", type=int, default=100)
    p.add_argument("--cache", default="BengaluruOSMCache.jsonl")
    a = p.parse_args()
    if not a.boundary and not a.allow_bbox:
        print("Supply --boundary district.geojson or explicitly use --allow-bbox.", file=sys.stderr); return 2
    if a.tile_size <= a.min_tile_size or a.min_tile_size <= 0:
        print("--tile-size must be greater than --min-tile-size.", file=sys.stderr); return 2
    boundary = load_boundary(a.boundary) if a.boundary else None
    s,w,n,e = DEFAULT_BBOX; tiles=[]; y=s
    while y < n:
        y2=min(y+a.tile_size,n); x=w
        while x < e:
            x2=min(x+a.tile_size,e); tiles.append((y,x,y2,x2)); x=x2
        y=y2
    cache=Path(a.cache); data=load_cache(cache)
    print(f"Loaded {len(data):,} cached unique OSM elements.")
    print(f"Starting {len(tiles)} tiles. Successful results are saved for future runs.")
    failed=[]
    def collect(tile):
        try:
            result=fetch(query_for(tile), a.request_timeout)
            fresh=[]
            for el in result.get("elements", []):
                k=(el.get("type"),el.get("id"))
                if k[0] and k[1] is not None and k not in data:
                    data[k]=el; fresh.append(el)
            if fresh: append_cache(cache, fresh)
            print(f"    Success: +{len(fresh):,} new; {len(data):,} cached total.")
            time.sleep(1.2)
        except Exception as exc:
            size=max(tile[2]-tile[0], tile[3]-tile[1])
            if size/2 >= a.min_tile_size:
                print(f"    Request failed; splitting tile ({type(exc).__name__}).")
                for child in split(tile): collect(child)
            else:
                print(f"    Small tile failed; will retry next run: {exc}")
                failed.append(tile); time.sleep(2)
    for i,t in enumerate(tiles,1):
        print(f"[{i}/{len(tiles)}] Tile {','.join(f'{v:.5f}' for v in t)}")
        collect(t)
    rows=write_csv(data, a.out, boundary)
    counts={}
    for r in rows: counts[r["category"]]=counts.get(r["category"],0)+1
    print(f"\\nCSV updated: {Path(a.out).resolve()}")
    print(f"Cached elements: {len(data):,}; rows in study area: {len(rows):,}")
    for k,v in sorted(counts.items()): print(f"  {k:20s} {v:>8,}")
    if failed: print(f"\\n{len(failed)} small tiles failed. Run the same command again; successful tiles remain cached.")
    if not boundary: print("\\nWARNING: bounding-box extract only; not exact district clipping.")
    if len(rows)<a.min_records:
        print(f"\\nBelow target of {a.min_records:,}. Do not add synthetic records.")
        return 1
    print("\\n10,000-record threshold reached. Validate records before database import.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
