#!/usr/bin/env python3
"""
Convert GeoJSON files to FlatGeobuf format for much faster loading
"""

import geopandas as gpd
import os
import time

def convert_to_flatgeobuf(input_file, output_file):
    """Convert GeoJSON to FlatGeobuf format"""

    print(f"Converting {input_file} to FlatGeobuf...")

    # Load GeoJSON
    start_time = time.time()
    gdf = gpd.read_file(input_file)
    load_time = time.time() - start_time

    print(f"  Loaded {len(gdf)} features in {load_time:.2f}s")

    # Save as FlatGeobuf
    start_time = time.time()
    gdf.to_file(output_file, driver='FlatGeobuf')
    save_time = time.time() - start_time

    print(f"  Saved FlatGeobuf in {save_time:.2f}s")

    # Compare file sizes
    original_size = os.path.getsize(input_file)
    fgb_size = os.path.getsize(output_file)
    size_reduction = (1 - fgb_size / original_size) * 100

    print(f"  Original size: {original_size / (1024*1024):.2f} MB")
    print(f"  FlatGeobuf size: {fgb_size / (1024*1024):.2f} MB")
    print(f"  Size reduction: {size_reduction:.1f}%")

    return output_file

def test_loading_performance(geojson_file, fgb_file):
    """Test loading performance comparison"""

    print(f"\n=== Performance Test ===")

    # Test GeoJSON loading
    print("Testing GeoJSON loading...")
    start_time = time.time()
    gdf_json = gpd.read_file(geojson_file)
    geojson_time = time.time() - start_time
    print(f"  GeoJSON load time: {geojson_time:.2f}s")

    # Test FlatGeobuf loading
    print("Testing FlatGeobuf loading...")
    start_time = time.time()
    gdf_fgb = gpd.read_file(fgb_file)
    fgb_time = time.time() - start_time
    print(f"  FlatGeobuf load time: {fgb_time:.2f}s")

    # Calculate speedup
    speedup = geojson_time / fgb_time if fgb_time > 0 else float('inf')
    print(f"  Speedup: {speedup:.1f}x faster")

    # Verify data integrity
    print(f"  Features match: {len(gdf_json) == len(gdf_fgb)}")

def main():
    """Convert all road files to FlatGeobuf"""

    files_to_convert = [
        ('motorways_wgs84.geojson', 'motorways.fgb'),
        ('motorways_compressed.geojson', 'motorways_compressed.fgb'),
        ('a1_to_a299_compressed.geojson', 'a1_to_a299.fgb')
    ]

    print("Converting road datasets to FlatGeobuf format...")
    print("="*50)

    for input_file, output_file in files_to_convert:
        if os.path.exists(input_file):
            convert_to_flatgeobuf(input_file, output_file)
            print()
        else:
            print(f"Skipping {input_file} - file not found")
            print()

    # Test performance with the largest file
    if os.path.exists('a1_to_a299_compressed.geojson') and os.path.exists('a1_to_a299.fgb'):
        test_loading_performance('a1_to_a299_compressed.geojson', 'a1_to_a299.fgb')

if __name__ == "__main__":
    main()