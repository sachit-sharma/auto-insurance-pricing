#!/usr/bin/env python3
"""
Fetch Belgium's province boundaries (Natural Earth, admin-1 level) and cache
them as a small GeoJSON for mapping.

Natural Earth only digitizes admin-1 boundaries for a handful of large
countries at 50m resolution (US, Canada, Brazil, Russia, etc.) - small
countries like Belgium only appear in the 10m dataset. We download the full
10m admin-1 shapefile once (~15MB, cached in .tmp/), filter to Belgium, and
write out an 11-feature GeoJSON (10 provinces + Brussels-Capital) so later
reads are instant and don't require geopandas to re-parse the global file.

Usage:
    python3 tools/fetch_belgium_provinces.py [output_geojson_path]

Example:
    python3 tools/fetch_belgium_provinces.py .tmp/belgium_provinces.geojson
"""
import sys
from pathlib import Path
from urllib.request import urlretrieve

import geopandas as gpd

NATURAL_EARTH_URL = "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_1_states_provinces.zip"

repo_root = Path(__file__).resolve().parent.parent
cache_dir = repo_root / ".tmp"
cache_dir.mkdir(exist_ok=True)
cached_zip = cache_dir / "ne_10m_admin_1_states_provinces.zip"

output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else cache_dir / "belgium_provinces.geojson"


def main():
    if not cached_zip.exists():
        print("Downloading Natural Earth admin-1 boundaries (~15MB, one-time)...")
        urlretrieve(NATURAL_EARTH_URL, cached_zip)

    gdf = gpd.read_file(f"zip://{cached_zip}")
    belgium = gdf[gdf["adm0_a3"] == "BEL"][["name", "name_en", "type_en", "geometry"]]

    if belgium.empty:
        raise SystemExit("No Belgium features found - check adm0_a3 filter against the shapefile schema.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    belgium.to_file(output_path, driver="GeoJSON")
    print(f"Wrote {len(belgium)} province features to {output_path}")


if __name__ == "__main__":
    main()
