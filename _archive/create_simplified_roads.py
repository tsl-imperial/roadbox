#!/usr/bin/env python3
"""
Create simplified version of roads for faster web viewing
"""

import geopandas as gpd
import json

def simplify_roads():
    """Create simplified road data for web performance"""
    print("Creating simplified roads for web viewer...")

    # Read the major roads
    gdf = gpd.read_file('major_roads_uk.gpkg')
    print(f"Original roads: {len(gdf):,}")

    # Simplify geometries (reduce coordinate precision)
    print("Simplifying geometries...")
    gdf['geometry'] = gdf['geometry'].simplify(tolerance=50)  # 50m tolerance

    # Keep only essential columns
    essential_cols = [
        'road_classification',
        'road_classification_number',
        'name_1',
        'length',
        'geometry'
    ]

    # Filter columns that exist
    available_cols = [col for col in essential_cols if col in gdf.columns]
    gdf_simplified = gdf[available_cols].copy()

    # Create motorway-only version for faster initial load
    motorways = gdf_simplified[gdf_simplified['road_classification'] == 'Motorway'].copy()
    print(f"Motorways: {len(motorways):,}")

    # Save motorways only (very fast)
    motorways.to_file('motorways_only.geojson', driver='GeoJSON')
    print("Saved motorways_only.geojson")

    # Create major A roads only (A1-A99)
    a_roads = gdf_simplified[gdf_simplified['road_classification'] == 'A Road'].copy()
    if 'road_classification_number' in a_roads.columns:
        # Extract A road numbers and filter for major ones
        a_roads['a_number'] = a_roads['road_classification_number'].str.extract(r'A(\d+)').astype(float, errors='ignore')
        major_a_roads = a_roads[a_roads['a_number'] <= 99].copy()  # A1-A99 only
        print(f"Major A roads (A1-A99): {len(major_a_roads):,}")

        major_a_roads.to_file('major_a_roads.geojson', driver='GeoJSON')
        print("Saved major_a_roads.geojson")

    # Combined major roads (motorways + A1-A99)
    if 'major_a_roads' in locals():
        import pandas as pd
        combined = pd.concat([motorways, major_a_roads], ignore_index=True)
        combined = gpd.GeoDataFrame(combined)
        combined.to_file('major_roads_simplified.geojson', driver='GeoJSON')
        print(f"Saved major_roads_simplified.geojson ({len(combined):,} roads)")

    return len(gdf), len(motorways), len(major_a_roads) if 'major_a_roads' in locals() else 0

def main():
    try:
        original, motorways, major_a = simplify_roads()
        print(f"\nSimplification complete:")
        print(f"  Original: {original:,} roads")
        print(f"  Motorways only: {motorways:,} roads")
        print(f"  Major A roads: {major_a:,} roads")
        print(f"  Combined simplified: {motorways + major_a:,} roads")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()