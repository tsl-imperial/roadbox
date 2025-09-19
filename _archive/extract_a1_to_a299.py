#!/usr/bin/env python3
"""
Extract A1 to A299 roads and compress them
"""

import geopandas as gpd
import os

def extract_and_compress_a1_to_a299():
    """Extract A1 to A299 roads and compress them"""

    print("Loading road_link layer...")
    gdf = gpd.read_file('oproad_gb.gpkg', layer='road_link')

    print(f"Total road links: {len(gdf)}")
    print(f"Coordinate system: {gdf.crs}")

    # Extract A1 to A299 roads
    a1_to_a299_roads = gdf[
        gdf['road_classification_number'].str.match(r'^A([1-9]|[1-9]\d|1\d\d|2\d\d)$', na=False)
    ].copy()

    print(f"A1-A299 road segments: {len(a1_to_a299_roads)}")

    # Show A road range
    a_road_numbers = a1_to_a299_roads['road_classification_number'].unique()
    a_road_nums = []
    for road in a_road_numbers:
        try:
            num = int(road[1:])  # Remove 'A' prefix
            if 1 <= num <= 299:  # Double check range
                a_road_nums.append(num)
        except:
            pass

    if a_road_nums:
        a_road_nums.sort()
        print(f"A road range: A{min(a_road_nums)} to A{max(a_road_nums)}")
        print(f"Total unique A roads: {len(a_road_nums)}")

    # Convert to WGS84
    print("Converting to WGS84...")
    a1_to_a299_wgs84 = a1_to_a299_roads.to_crs('EPSG:4326')

    # Save uncompressed version first
    uncompressed_file = 'a1_to_a299_wgs84.geojson'
    print(f"Saving uncompressed A1-A299 roads...")
    a1_to_a299_wgs84.to_file(uncompressed_file, driver='GeoJSON')

    uncompressed_size = os.path.getsize(uncompressed_file)
    print(f"Uncompressed A1-A299 roads: {uncompressed_size / (1024*1024):.2f} MB")

    # Count original coordinates
    original_coords = 0
    for geom in a1_to_a299_wgs84.geometry:
        if geom.geom_type == 'LineString':
            original_coords += len(geom.coords)
        elif geom.geom_type == 'MultiLineString':
            for line in geom.geoms:
                original_coords += len(line.coords)

    print(f"Original coordinate points: {original_coords:,}")

    # Apply compression
    print(f"\nApplying compression...")
    print(f"  Douglas-Peucker tolerance: 0.001 degrees (~111m)")
    print(f"  Coordinate precision: 4 decimal places")

    compressed_geometries = []
    simplified_coords = 0

    for i, geom in enumerate(a1_to_a299_wgs84.geometry):
        if i % 5000 == 0:
            print(f"  Processing segment {i}/{len(a1_to_a299_wgs84)}")

        # Apply Douglas-Peucker simplification
        simplified_geom = geom.simplify(tolerance=0.001, preserve_topology=True)

        # Reduce coordinate precision
        if simplified_geom.geom_type == 'LineString':
            coords = [[round(x, 4), round(y, 4)] for x, y in simplified_geom.coords]
            if len(coords) >= 2:  # Valid LineString needs at least 2 points
                simplified_geom = type(simplified_geom)(coords)
                simplified_coords += len(coords)
            else:
                simplified_geom = geom  # Fallback to original
                if geom.geom_type == 'LineString':
                    simplified_coords += len(geom.coords)

        elif simplified_geom.geom_type == 'MultiLineString':
            simplified_lines = []
            for line in simplified_geom.geoms:
                coords = [[round(x, 4), round(y, 4)] for x, y in line.coords]
                if len(coords) >= 2:
                    simplified_lines.append(type(line)(coords))
                    simplified_coords += len(coords)

            if simplified_lines:
                simplified_geom = type(simplified_geom)(simplified_lines)
            else:
                simplified_geom = geom  # Fallback to original
                for line in geom.geoms:
                    simplified_coords += len(line.coords)

        compressed_geometries.append(simplified_geom)

    # Create compressed GeoDataFrame
    compressed_gdf = a1_to_a299_wgs84.copy()
    compressed_gdf.geometry = compressed_geometries

    # Save compressed version
    compressed_file = 'a1_to_a299_compressed.geojson'
    print(f"\nSaving compressed A1-A299 roads...")
    compressed_gdf.to_file(compressed_file, driver='GeoJSON')

    # Calculate compression statistics
    compressed_size = os.path.getsize(compressed_file)
    size_reduction = (1 - compressed_size / uncompressed_size) * 100
    coord_reduction = (1 - simplified_coords / original_coords) * 100

    print(f"\nCompression Results:")
    print(f"  Uncompressed size: {uncompressed_size / (1024*1024):.2f} MB")
    print(f"  Compressed size: {compressed_size / (1024*1024):.2f} MB")
    print(f"  Size reduction: {size_reduction:.1f}%")
    print(f"  ")
    print(f"  Original coordinates: {original_coords:,}")
    print(f"  Compressed coordinates: {simplified_coords:,}")
    print(f"  Coordinate reduction: {coord_reduction:.1f}%")
    print(f"  ")
    print(f"  Segments: {len(a1_to_a299_wgs84)} (unchanged)")

    # Show A road statistics by number range
    print(f"\nA Road Statistics:")
    ranges = [
        (1, 99, "Major A roads (A1-A99)"),
        (100, 199, "A100-A199"),
        (200, 299, "A200-A299 (includes A282)")
    ]

    for start, end, label in ranges:
        roads_in_range = []
        for road in a_road_numbers:
            try:
                num = int(road[1:])
                if start <= num <= end:
                    roads_in_range.append(road)
            except:
                pass

        if roads_in_range:
            segments_in_range = compressed_gdf[
                compressed_gdf['road_classification_number'].isin(roads_in_range)
            ]
            print(f"  {label}: {len(roads_in_range)} roads, {len(segments_in_range)} segments")

    # Check specifically for A282 (Dartford Crossing)
    a282_segments = compressed_gdf[compressed_gdf['road_classification_number'] == 'A282']
    print(f"\n✅ A282 (Dartford Crossing): {len(a282_segments)} segments included")

    return compressed_file

if __name__ == "__main__":
    extract_and_compress_a1_to_a299()