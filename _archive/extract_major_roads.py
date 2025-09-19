#!/usr/bin/env python3
"""
Extract A Roads and Motorways from the UK road network
"""

import geopandas as gpd
import matplotlib.pyplot as plt

def extract_major_roads():
    """Extract A Roads and Motorways from the GeoPackage"""
    print("Extracting A Roads and Motorways from oproad_gb.gpkg...")

    # Read road_link layer
    gdf = gpd.read_file('oproad_gb.gpkg', layer='road_link')
    print(f"Total roads: {len(gdf):,}")

    # Filter for A Roads and Motorways
    major_roads = gdf[gdf['road_classification'].isin(['A Road', 'Motorway'])].copy()
    print(f"Major roads found: {len(major_roads):,}")

    # Breakdown by type
    road_counts = major_roads['road_classification'].value_counts()
    print("\nBreakdown:")
    for road_type, count in road_counts.items():
        print(f"  {road_type}: {count:,}")

    # Show road numbers
    if 'road_classification_number' in major_roads.columns:
        print(f"\nTop roads by segment count:")
        road_numbers = major_roads['road_classification_number'].value_counts()
        print(road_numbers.head(15))

    # Calculate total length
    if 'length' in major_roads.columns:
        total_length = major_roads['length'].sum()
        print(f"\nTotal major road length: {total_length:,.0f} meters ({total_length/1000:,.0f} km)")

        # Length by type
        length_by_type = major_roads.groupby('road_classification')['length'].sum()
        print("\nLength by road type:")
        for road_type, length in length_by_type.items():
            print(f"  {road_type}: {length:,.0f} meters ({length/1000:,.0f} km)")

    return major_roads

def visualize_major_roads(major_roads):
    """Create visualization of major roads"""
    fig, axes = plt.subplots(1, 2, figsize=(20, 10))

    # All major roads
    major_roads.plot(ax=axes[0], linewidth=0.5, alpha=0.8)
    axes[0].set_title(f"UK Major Roads Network ({len(major_roads):,} segments)")
    axes[0].set_axis_off()

    # Color by road type
    major_roads.plot(ax=axes[1], column='road_classification',
                    legend=True, linewidth=0.6, alpha=0.9,
                    cmap='Set1')
    axes[1].set_title("Major Roads by Type (A Roads vs Motorways)")
    axes[1].set_axis_off()

    plt.tight_layout()
    plt.savefig('major_roads_uk.png', dpi=150, bbox_inches='tight')
    plt.show()

def save_major_roads(major_roads):
    """Save major roads to new files"""
    # Save as GeoPackage
    major_roads.to_file('major_roads_uk.gpkg', driver='GPKG')
    print("Major roads saved as 'major_roads_uk.gpkg'")

    # Save as GeoJSON
    major_roads.to_file('major_roads_uk.geojson', driver='GeoJSON')
    print("Major roads saved as 'major_roads_uk.geojson'")

    # Save as Shapefile
    major_roads.to_file('major_roads_uk.shp', driver='ESRI Shapefile')
    print("Major roads saved as 'major_roads_uk.shp'")

def main():
    print("UK Major Roads Extractor")
    print("=======================")

    major_roads = extract_major_roads()

    print("\nCreating visualization...")
    visualize_major_roads(major_roads)

    print("\nSaving major roads to files...")
    save_major_roads(major_roads)

    print(f"\nComplete! Files created:")
    print(f"  - major_roads_uk.gpkg (GeoPackage)")
    print(f"  - major_roads_uk.geojson (GeoJSON)")
    print(f"  - major_roads_uk.shp (Shapefile)")
    print(f"  - major_roads_uk.png (Visualization)")

if __name__ == "__main__":
    main()