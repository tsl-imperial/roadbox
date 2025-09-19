#!/usr/bin/env python3
"""
Create Level-of-Detail (LOD) datasets for efficient web loading
"""

import geopandas as gpd
import os

def create_lod_datasets():
    """Create different detail levels for progressive loading"""

    print("Creating Level-of-Detail datasets...")

    # Load the full A1-A299 dataset
    print("Loading full A1-A299 dataset...")
    gdf = gpd.read_file('a1_to_a299_compressed.geojson')

    print(f"Total segments: {len(gdf)}")

    # Level 1: Major roads only (A1-A99) - Load first
    print("\nCreating Level 1: Major roads (A1-A99)...")
    major_roads = gdf[
        gdf['road_classification_number'].str.match(r'^A([1-9]|[1-9]\d)$', na=False)
    ].copy()

    major_file = 'roads_level1_major.geojson'
    major_roads.to_file(major_file, driver='GeoJSON')
    major_size = os.path.getsize(major_file)

    print(f"  Level 1: {len(major_roads)} segments, {major_size / (1024*1024):.2f} MB")

    # Level 2: A100-A199 - Load on zoom in
    print("Creating Level 2: A100-A199...")
    a100_roads = gdf[
        gdf['road_classification_number'].str.match(r'^A1\d\d$', na=False)
    ].copy()

    a100_file = 'roads_level2_a100.geojson'
    a100_roads.to_file(a100_file, driver='GeoJSON')
    a100_size = os.path.getsize(a100_file)

    print(f"  Level 2: {len(a100_roads)} segments, {a100_size / (1024*1024):.2f} MB")

    # Level 3: A200-A299 - Load on further zoom
    print("Creating Level 3: A200-A299...")
    a200_roads = gdf[
        gdf['road_classification_number'].str.match(r'^A2\d\d$', na=False)
    ].copy()

    a200_file = 'roads_level3_a200.geojson'
    a200_roads.to_file(a200_file, driver='GeoJSON')
    a200_size = os.path.getsize(a200_file)

    print(f"  Level 3: {len(a200_roads)} segments, {a200_size / (1024*1024):.2f} MB")

    # Summary
    total_lod_size = major_size + a100_size + a200_size
    original_size = os.path.getsize('a1_to_a299_compressed.geojson')

    print(f"\nLOD Summary:")
    print(f"  Original file: {original_size / (1024*1024):.2f} MB (loads all at once)")
    print(f"  LOD files total: {total_lod_size / (1024*1024):.2f} MB")
    print(f"  Initial load (Level 1): {major_size / (1024*1024):.2f} MB")
    print(f"  Progressive loading: Load only what's needed!")

    return [major_file, a100_file, a200_file]

if __name__ == "__main__":
    create_lod_datasets()