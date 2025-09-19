#!/usr/bin/env python3
"""
Quick check of motorway network connectivity
"""

import geopandas as gpd
import json
from collections import defaultdict, deque
import numpy as np

def quick_motorway_connectivity():
    """Quick check if motorway network is connected"""

    print("Loading motorways...")
    gdf = gpd.read_file('motorways_wgs84.geojson')
    print(f"Total segments: {len(gdf)}")

    # Group by motorway number
    motorway_groups = defaultdict(list)
    for idx, row in gdf.iterrows():
        road_num = row['road_classification_number'] or 'Unknown'
        motorway_groups[road_num].append(idx)

    print(f"\nMotorway breakdown:")
    for road, segments in sorted(motorway_groups.items()):
        print(f"  {road}: {len(segments)} segments")

    # Simple spatial connectivity check
    # Build a grid-based spatial index for faster lookups
    print(f"\nSpatial connectivity analysis...")

    # Get all segment bounds
    bounds_list = []
    for idx, row in gdf.iterrows():
        bounds = row.geometry.bounds  # (minx, miny, maxx, maxy)
        bounds_list.append((idx, bounds))

    # Check for overlapping/touching segments
    connected_pairs = set()
    tolerance = 0.001  # About 100m

    print("Finding connected segments...")
    for i, (idx1, bounds1) in enumerate(bounds_list):
        if i % 100 == 0:
            print(f"  Processed {i}/{len(bounds_list)} segments")

        for j, (idx2, bounds2) in enumerate(bounds_list[i+1:], i+1):
            # Quick bounds check
            if (abs(bounds1[0] - bounds2[2]) <= tolerance or  # minx1 vs maxx2
                abs(bounds1[2] - bounds2[0]) <= tolerance or  # maxx1 vs minx2
                abs(bounds1[1] - bounds2[3]) <= tolerance or  # miny1 vs maxy2
                abs(bounds1[3] - bounds2[1]) <= tolerance):   # maxy1 vs miny2

                # Check if geometries actually touch/intersect
                geom1 = gdf.iloc[idx1].geometry
                geom2 = gdf.iloc[idx2].geometry

                if geom1.distance(geom2) <= tolerance:
                    connected_pairs.add((idx1, idx2))

    print(f"Found {len(connected_pairs)} connected segment pairs")

    # Build graph
    graph = defaultdict(set)
    for idx1, idx2 in connected_pairs:
        graph[idx1].add(idx2)
        graph[idx2].add(idx1)

    # Find connected components
    visited = set()
    components = []

    for start_idx in range(len(gdf)):
        if start_idx not in visited:
            # BFS
            component = []
            queue = deque([start_idx])
            visited.add(start_idx)

            while queue:
                node = queue.popleft()
                component.append(node)

                for neighbor in graph[node]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            components.append(component)

    print(f"\nConnectivity Results:")
    print(f"Connected components: {len(components)}")

    if len(components) == 1:
        print("✅ Motorways form a SINGLE connected network!")
    else:
        print("❌ Motorways are split into multiple networks")

        # Show largest components
        sorted_components = sorted(components, key=len, reverse=True)
        for i, comp in enumerate(sorted_components[:5]):
            print(f"  Component {i+1}: {len(comp)} segments")

            # Show which motorways are in this component
            motorways_in_comp = defaultdict(int)
            for seg_idx in comp:
                road_num = gdf.iloc[seg_idx]['road_classification_number'] or 'Unknown'
                motorways_in_comp[road_num] += 1

            print(f"    Contains: {', '.join(sorted(motorways_in_comp.keys()))}")

if __name__ == "__main__":
    quick_motorway_connectivity()