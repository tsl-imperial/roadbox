#!/usr/bin/env python3
"""
Extract complete M25 including A282 Dartford Crossing
"""

import geopandas as gpd

def extract_complete_motorways():
    """Extract motorways including A282 to complete M25 ring"""

    print("Loading road_link layer...")
    gdf = gpd.read_file('oproad_gb.gpkg', layer='road_link')

    print(f"Total road links: {len(gdf)}")
    print(f"Coordinate system: {gdf.crs}")

    # Extract motorways (original filter)
    motorways = gdf[gdf['road_classification_number'].str.startswith('M', na=False)].copy()
    print(f"Motorway segments: {len(motorways)}")

    # Extract A(M) roads (motorway sections of A roads)
    a_motorways = gdf[
        gdf['road_classification_number'].str.contains(r'A\d+\(M\)', regex=True, na=False)
    ].copy()
    print(f"A(M) road segments: {len(a_motorways)}")

    # Extract A282 (Dartford Crossing - completes M25 ring)
    a282_roads = gdf[gdf['road_classification_number'] == 'A282'].copy()
    print(f"A282 segments: {len(a282_roads)}")

    # Combine all motorway-type roads
    all_motorways = pd.concat([motorways, a_motorways, a282_roads], ignore_index=True)
    print(f"Total motorway-type segments: {len(all_motorways)}")

    # Convert to WGS84 for web display
    print("Converting to WGS84...")
    all_motorways_wgs84 = all_motorways.to_crs('EPSG:4326')

    # Save complete motorway network
    output_file = 'complete_motorways_wgs84.geojson'
    all_motorways_wgs84.to_file(output_file, driver='GeoJSON')
    print(f"Complete motorway network saved to: {output_file}")

    # Show breakdown
    print(f"\nBreakdown by road type:")
    road_counts = all_motorways_wgs84['road_classification_number'].value_counts()
    for road, count in road_counts.head(20).items():
        print(f"  {road}: {count} segments")

    return output_file

if __name__ == "__main__":
    import pandas as pd
    extract_complete_motorways()