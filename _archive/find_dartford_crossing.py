#!/usr/bin/env python3
"""
Find the missing Dartford Crossing (M25 bridge/tunnel)
"""

import geopandas as gpd
import pandas as pd

def find_dartford_crossing():
    """Look for the Dartford Crossing specifically"""

    print("Loading road_link layer...")
    gdf = gpd.read_file('oproad_gb.gpkg', layer='road_link')

    print(f"Total road links: {len(gdf)}")

    # Check road_structure values
    print(f"\nRoad structure types:")
    structure_counts = gdf['road_structure'].value_counts()
    print(structure_counts.head(10))

    # Look for M25 entries
    print(f"\n=== M25 Analysis ===")
    m25_roads = gdf[gdf['road_classification_number'] == 'M25'].copy()
    print(f"Total M25 segments: {len(m25_roads)}")

    # Check M25 road structures
    if len(m25_roads) > 0:
        print(f"\nM25 road structures:")
        m25_structures = m25_roads['road_structure'].value_counts()
        print(m25_structures)

        # Look for bridges/tunnels specifically
        bridge_tunnel_m25 = m25_roads[
            m25_roads['road_structure'].isin(['Bridge', 'Tunnel', 'bridge', 'tunnel']) |
            m25_roads['road_structure'].str.contains('Bridge|Tunnel|bridge|tunnel', case=False, na=False)
        ]

        print(f"\nM25 bridges/tunnels: {len(bridge_tunnel_m25)}")
        if len(bridge_tunnel_m25) > 0:
            for _, row in bridge_tunnel_m25.iterrows():
                print(f"  - {row['name_1']} ({row['road_structure']}) - {row['length']}m")

    # Search for Dartford specifically
    print(f"\n=== Dartford Search ===")
    dartford_roads = gdf[
        gdf['name_1'].str.contains('Dartford', case=False, na=False) |
        gdf['name_2'].str.contains('Dartford', case=False, na=False)
    ]

    print(f"Roads with 'Dartford' in name: {len(dartford_roads)}")
    for _, row in dartford_roads.head(10).iterrows():
        print(f"  - {row['name_1']} ({row['road_classification_number']}) - {row['road_structure']}")

    # Search for Queen Elizabeth Bridge
    print(f"\n=== Queen Elizabeth Bridge Search ===")
    qe_roads = gdf[
        gdf['name_1'].str.contains('Queen Elizabeth|QE2|QEII', case=False, na=False) |
        gdf['name_2'].str.contains('Queen Elizabeth|QE2|QEII', case=False, na=False)
    ]

    print(f"Queen Elizabeth bridge roads: {len(qe_roads)}")
    for _, row in qe_roads.head(10).iterrows():
        print(f"  - {row['name_1']} ({row['road_classification_number']}) - {row['road_structure']}")

    # Check if our original extraction missed anything
    print(f"\n=== Original Filter Check ===")
    original_filter = (gdf['road_classification_number'] == 'M25')
    print(f"Roads matching our original M25 filter: {original_filter.sum()}")

    # Check for M25 with different structures
    m25_with_structure = gdf[
        (gdf['road_classification_number'] == 'M25') &
        (gdf['road_structure'].notna())
    ]

    print(f"M25 roads with structure info: {len(m25_with_structure)}")
    if len(m25_with_structure) > 0:
        print("Structure breakdown:")
        for structure, count in m25_with_structure['road_structure'].value_counts().items():
            print(f"  {structure}: {count}")

    # Look for Thames crossing roads near London
    print(f"\n=== Thames Crossing Search ===")

    # Get rough Thames crossing area (around Dartford)
    # Dartford is approximately at 51.4N, 0.2E
    bbox_filter = (
        (gdf.geometry.bounds['minx'] > -0.5) &
        (gdf.geometry.bounds['maxx'] < 0.5) &
        (gdf.geometry.bounds['miny'] > 51.3) &
        (gdf.geometry.bounds['maxy'] < 51.6)
    )

    thames_area = gdf[bbox_filter]

    # Look for major roads crossing the Thames
    major_thames_roads = thames_area[
        (thames_area['road_classification_number'].isin(['M25', 'A282'])) |
        (thames_area['name_1'].str.contains('M25|A282|Dartford|Queen Elizabeth', case=False, na=False))
    ]

    print(f"Major roads in Thames crossing area: {len(major_thames_roads)}")
    for _, row in major_thames_roads.head(10).iterrows():
        bounds = row.geometry.bounds
        print(f"  - {row['road_classification_number']} {row['name_1']} ({row['road_structure']}) at {bounds[1]:.3f}N")

if __name__ == "__main__":
    find_dartford_crossing()