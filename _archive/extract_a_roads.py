#!/usr/bin/env python3
"""
Extract only A Roads from the UK road network
"""

import geopandas as gpd
import matplotlib.pyplot as plt

def extract_a_roads():
    """Extract A Roads from the GeoPackage"""
    print("Extracting A Roads from oproad_gb.gpkg...")

    # Read road_link layer
    gdf = gpd.read_file('oproad_gb.gpkg', layer='road_link')
    print(f"Total roads: {len(gdf):,}")

    # Filter for A Roads
    a_roads = gdf[gdf['road_classification'] == 'A Road'].copy()
    print(f"A Roads found: {len(a_roads):,}")

    # Show A Road numbers
    if 'road_classification_number' in a_roads.columns:
        a_road_numbers = a_roads['road_classification_number'].value_counts()
        print(f"\nTop A Roads by segment count:")
        print(a_road_numbers.head(10))
        print(f"Total unique A Roads: {a_road_numbers.count()}")

    # Calculate total length
    if 'length' in a_roads.columns:
        total_length = a_roads['length'].sum()
        print(f"\nTotal A Road length: {total_length:,.0f} meters ({total_length/1000:,.0f} km)")

    return a_roads

def visualize_a_roads(a_roads):
    """Create visualization of A Roads"""
    fig, axes = plt.subplots(1, 2, figsize=(20, 10))

    # Basic A Roads map
    a_roads.plot(ax=axes[0], linewidth=0.5, color='red', alpha=0.8)
    axes[0].set_title(f"UK A Roads Network ({len(a_roads):,} segments)")
    axes[0].set_axis_off()

    # Color by A Road number (show major ones)
    if 'road_classification_number' in a_roads.columns:
        # Get top 20 A roads by segment count for coloring
        top_roads = a_roads['road_classification_number'].value_counts().head(20).index
        a_roads_subset = a_roads[a_roads['road_classification_number'].isin(top_roads)]

        a_roads_subset.plot(ax=axes[1], column='road_classification_number',
                           legend=True, linewidth=0.8, alpha=0.9, cmap='tab20')
        axes[1].set_title(f"Top 20 A Roads by Segment Count")
        axes[1].set_axis_off()
    else:
        # Fallback: just show all A roads
        a_roads.plot(ax=axes[1], linewidth=0.5, color='blue', alpha=0.8)
        axes[1].set_title("A Roads Network")
        axes[1].set_axis_off()

    plt.tight_layout()
    plt.savefig('a_roads_only.png', dpi=150, bbox_inches='tight')
    plt.show()

def save_a_roads(a_roads):
    """Save A Roads to new files"""
    # Save as GeoPackage
    a_roads.to_file('a_roads_uk.gpkg', driver='GPKG')
    print("A Roads saved as 'a_roads_uk.gpkg'")

    # Save as GeoJSON for web use
    a_roads.to_file('a_roads_uk.geojson', driver='GeoJSON')
    print("A Roads saved as 'a_roads_uk.geojson'")

def main():
    print("UK A Roads Extractor")
    print("===================")

    a_roads = extract_a_roads()

    print("\nCreating visualization...")
    visualize_a_roads(a_roads)

    print("\nSaving A Roads to separate files...")
    save_a_roads(a_roads)

    print(f"\nComplete! A Roads visualization saved as 'a_roads_only.png'")

if __name__ == "__main__":
    main()