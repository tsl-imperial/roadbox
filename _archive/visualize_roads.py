#!/usr/bin/env python3
"""
Quick road visualization tool for UK road datasets
Supports shapefile (.shp) and can be extended for PBF files
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import argparse

def analyze_shapefile(shapefile_path):
    """Analyze and visualize shapefile road data"""
    print(f"Loading shapefile: {shapefile_path}")

    # Load the shapefile
    gdf = gpd.read_file(shapefile_path)

    print(f"Total features: {len(gdf)}")
    print(f"CRS: {gdf.crs}")
    print(f"Bounds: {gdf.total_bounds}")

    # Show column info
    print("\nColumns:")
    for col in gdf.columns:
        if col != 'geometry':
            print(f"  {col}: {gdf[col].dtype}")
            if gdf[col].dtype == 'object':
                unique_vals = gdf[col].unique()
                if len(unique_vals) <= 20:
                    print(f"    Unique values: {list(unique_vals)}")
                else:
                    print(f"    {len(unique_vals)} unique values")

    # Look for road type information
    road_type_cols = [col for col in gdf.columns if any(keyword in col.lower()
                     for keyword in ['type', 'class', 'highway', 'road', 'category'])]

    if road_type_cols:
        print(f"\nRoad type columns found: {road_type_cols}")
        for col in road_type_cols:
            print(f"\n{col} distribution:")
            print(gdf[col].value_counts().head(10))

    # Create visualization
    fig, axes = plt.subplots(1, 2, figsize=(15, 8))

    # Basic map
    gdf.plot(ax=axes[0], linewidth=0.5, alpha=0.7)
    axes[0].set_title("UK Road Network")
    axes[0].set_axis_off()

    # Color by road type if available
    if road_type_cols:
        main_type_col = road_type_cols[0]
        gdf.plot(column=main_type_col, ax=axes[1], legend=True,
                linewidth=0.8, alpha=0.8, cmap='tab10')
        axes[1].set_title(f"Roads by {main_type_col}")
        axes[1].set_axis_off()
    else:
        # Just show a zoomed view
        bounds = gdf.total_bounds
        center_x = (bounds[0] + bounds[2]) / 2
        center_y = (bounds[1] + bounds[3]) / 2
        zoom_factor = 0.1

        zoom_gdf = gdf.cx[center_x - zoom_factor * (bounds[2] - bounds[0]):
                          center_x + zoom_factor * (bounds[2] - bounds[0]),
                          center_y - zoom_factor * (bounds[3] - bounds[1]):
                          center_y + zoom_factor * (bounds[3] - bounds[1])]

        zoom_gdf.plot(ax=axes[1], linewidth=1.0, alpha=0.8)
        axes[1].set_title("Zoomed View")
        axes[1].set_axis_off()

    plt.tight_layout()
    plt.savefig('road_visualization.png', dpi=150, bbox_inches='tight')
    plt.show()

    return gdf

def main():
    parser = argparse.ArgumentParser(description='Visualize UK road datasets')
    parser.add_argument('--shapefile', default='Major_Road_Network_2018_Open_Roads.shp',
                       help='Path to shapefile')

    args = parser.parse_args()

    # Check if shapefile exists
    if Path(args.shapefile).exists():
        print("=== SHAPEFILE ANALYSIS ===")
        gdf = analyze_shapefile(args.shapefile)

        # Save summary
        with open('road_analysis_summary.txt', 'w') as f:
            f.write(f"Road Network Analysis Summary\n")
            f.write(f"============================\n\n")
            f.write(f"Total features: {len(gdf)}\n")
            f.write(f"CRS: {gdf.crs}\n")
            f.write(f"Bounds: {gdf.total_bounds}\n\n")

            f.write("Columns:\n")
            for col in gdf.columns:
                if col != 'geometry':
                    f.write(f"  {col}: {gdf[col].dtype}\n")

        print(f"\nVisualization saved as 'road_visualization.png'")
        print(f"Summary saved as 'road_analysis_summary.txt'")
    else:
        print(f"Shapefile not found: {args.shapefile}")

if __name__ == "__main__":
    main()