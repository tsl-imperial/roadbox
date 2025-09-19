#!/usr/bin/env python3
"""
Check if the motorway network is fully connected
"""

import geopandas as gpd
import json
from shapely.geometry import Point, LineString
from collections import defaultdict, deque
import numpy as np

def find_nearby_points(point, all_points, tolerance=0.0001):
    """Find points within tolerance distance"""
    nearby = []
    for i, other_point in enumerate(all_points):
        if point.distance(other_point) <= tolerance:
            nearby.append(i)
    return nearby

def check_motorway_connectivity():
    """Check if motorway network forms a connected graph"""

    print("Loading motorways data...")

    # Load the motorways GeoJSON
    gdf = gpd.read_file('motorways_wgs84.geojson')

    print(f"Total motorway segments: {len(gdf)}")

    # Extract all endpoints from all line segments
    all_endpoints = []
    segment_endpoints = []  # Track which endpoints belong to which segment

    for idx, row in gdf.iterrows():
        geom = row.geometry
        if geom.geom_type == 'LineString':
            start_point = Point(geom.coords[0])
            end_point = Point(geom.coords[-1])

            all_endpoints.extend([start_point, end_point])
            segment_endpoints.append((len(all_endpoints)-2, len(all_endpoints)-1))
        elif geom.geom_type == 'MultiLineString':
            segment_indices = []
            for line in geom.geoms:
                start_point = Point(line.coords[0])
                end_point = Point(line.coords[-1])
                all_endpoints.extend([start_point, end_point])
                segment_indices.extend([len(all_endpoints)-2, len(all_endpoints)-1])
            segment_endpoints.append(segment_indices)

    print(f"Total endpoints: {len(all_endpoints)}")

    # Build adjacency graph based on shared endpoints
    # Two segments are connected if they share an endpoint (within tolerance)
    tolerance = 0.0005  # ~50 meters

    # Find connections between segments
    graph = defaultdict(set)

    print("Building connectivity graph...")
    for i in range(len(gdf)):
        for j in range(i + 1, len(gdf)):
            # Get endpoints for segment i
            if isinstance(segment_endpoints[i], tuple):
                endpoints_i = [segment_endpoints[i][0], segment_endpoints[i][1]]
            else:
                endpoints_i = segment_endpoints[i]

            # Get endpoints for segment j
            if isinstance(segment_endpoints[j], tuple):
                endpoints_j = [segment_endpoints[j][0], segment_endpoints[j][1]]
            else:
                endpoints_j = segment_endpoints[j]

            # Check if any endpoint from i is close to any endpoint from j
            connected = False
            for ei in endpoints_i:
                for ej in endpoints_j:
                    if all_endpoints[ei].distance(all_endpoints[ej]) <= tolerance:
                        graph[i].add(j)
                        graph[j].add(i)
                        connected = True
                        break
                if connected:
                    break

    print(f"Graph has {len(graph)} nodes with connections")

    # Find connected components using BFS
    visited = set()
    components = []

    for start_node in range(len(gdf)):
        if start_node not in visited:
            # BFS to find all nodes in this component
            component = []
            queue = deque([start_node])
            visited.add(start_node)

            while queue:
                node = queue.popleft()
                component.append(node)

                for neighbor in graph[node]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            components.append(component)

    print(f"\nConnectivity Analysis:")
    print(f"Number of connected components: {len(components)}")
    print(f"Largest component size: {max(len(c) for c in components)}")
    print(f"Total segments: {len(gdf)}")

    if len(components) == 1:
        print("✅ The motorway network is FULLY CONNECTED!")
    else:
        print("❌ The motorway network is NOT fully connected")
        print(f"   Main component covers {max(len(c) for c in components)}/{len(gdf)} segments ({100*max(len(c) for c in components)/len(gdf):.1f}%)")

        # Show details of smaller components
        sorted_components = sorted(components, key=len, reverse=True)
        print("\nComponent sizes:")
        for i, comp in enumerate(sorted_components[:10]):  # Show top 10
            print(f"  Component {i+1}: {len(comp)} segments")
            if len(comp) <= 3:  # Show road names for small components
                for seg_idx in comp:
                    road_name = gdf.iloc[seg_idx]['road_classification_number'] or 'Unknown'
                    print(f"    - {road_name}")

    # Analyze specific motorway connectivity
    print(f"\nMotorway breakdown:")
    motorway_segments = defaultdict(list)
    for idx, row in gdf.iterrows():
        road_num = row['road_classification_number'] or 'Unknown'
        motorway_segments[road_num].append(idx)

    print(f"Number of distinct motorways: {len(motorway_segments)}")
    for road, segments in sorted(motorway_segments.items()):
        print(f"  {road}: {len(segments)} segments")

if __name__ == "__main__":
    check_motorway_connectivity()