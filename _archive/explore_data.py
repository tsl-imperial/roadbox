#!/usr/bin/env python3
"""
Data exploration tool for UK road shapefile collection
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import os

def explore_shapefiles():
    """Explore all shapefiles in the data directory"""
    data_dir = Path("data")
    shapefiles = list(data_dir.glob("*.shp"))

    print(f"Found {len(shapefiles)} shapefiles in data directory\n")

    # Group by prefix to understand the structure
    prefixes = {}
    for shp in shapefiles:
        prefix = shp.stem.split('_')[0]
        if prefix not in prefixes:
            prefixes[prefix] = []
        prefixes[prefix].append(shp.stem)

    print("File structure by prefix:")
    for prefix, files in sorted(prefixes.items()):
        print(f"  {prefix}: {len(files)} files")
        for f in sorted(files)[:5]:  # Show first 5
            print(f"    {f}")
        if len(files) > 5:
            print(f"    ... and {len(files) - 5} more")
        print()

    # Sample a few files for detailed analysis
    sample_files = shapefiles[:3]

    for shp_file in sample_files:
        print(f"=== ANALYZING: {shp_file.name} ===")
        try:
            gdf = gpd.read_file(shp_file)
            print(f"Features: {len(gdf)}")
            print(f"CRS: {gdf.crs}")
            print(f"Geometry type: {gdf.geometry.geom_type.unique()}")
            print(f"Bounds: {gdf.total_bounds}")

            print("Columns:")
            for col in gdf.columns:
                if col != 'geometry':
                    print(f"  {col}: {gdf[col].dtype}")
                    if gdf[col].dtype == 'object':
                        unique_vals = gdf[col].unique()
                        if len(unique_vals) <= 10:
                            print(f"    Values: {list(unique_vals)}")
                        else:
                            print(f"    {len(unique_vals)} unique values")
            print()

        except Exception as e:
            print(f"Error reading {shp_file}: {e}\n")

    return shapefiles

def create_overview_map(shapefiles):
    """Create an overview map of multiple shapefiles"""
    fig, ax = plt.subplots(1, 1, figsize=(15, 12))

    colors = plt.cm.tab10(range(len(shapefiles[:10])))  # Limit to 10 for visibility

    for i, shp_file in enumerate(shapefiles[:10]):
        try:
            gdf = gpd.read_file(shp_file)
            if not gdf.empty:
                gdf.plot(ax=ax, color=colors[i], alpha=0.7, linewidth=0.5,
                        label=shp_file.stem[:20])  # Truncate long names
        except Exception as e:
            print(f"Skipping {shp_file}: {e}")

    ax.set_title("UK Road Network - Multiple Datasets Overview")
    ax.set_axis_off()
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    plt.savefig('data_overview.png', dpi=150, bbox_inches='tight')
    plt.show()

def main():
    print("UK Road Data Explorer")
    print("====================\n")

    shapefiles = explore_shapefiles()

    # Create overview visualization
    print("Creating overview map...")
    create_overview_map(shapefiles)

    print(f"\nOverview map saved as 'data_overview.png'")
    print(f"Total shapefiles analyzed: {len(shapefiles)}")

if __name__ == "__main__":
    main()