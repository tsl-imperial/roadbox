#!/usr/bin/env python3
"""
Fast motorway connectivity check using NetworkX and spatial indexing
"""

import geopandas as gpd
import networkx as nx
from shapely.geometry import Point
from rtree import index
import numpy as np

def fast_motorway_connectivity():
    """Fast check using NetworkX and spatial indexing"""

    print("Loading motorways...")
    gdf = gpd.read_file('motorways_wgs84.geojson')
    print(f"Total segments: {len(gdf)}")

    # Extract endpoints with spatial index
    print("Building spatial index...")
    idx = index.Index()
    endpoints = {}  # point_id -> (x, y)
    segment_endpoints = {}  # segment_id -> [point_ids]

    point_id = 0
    tolerance = 0.0005  # ~50 meters

    for seg_id, row in gdf.iterrows():
        geom = row.geometry
        seg_points = []

        if geom.geom_type == 'LineString':
            coords = list(geom.coords)
            start = coords[0]
            end = coords[-1]

            for coord in [start, end]:
                # Check if we already have a nearby point
                nearby = list(idx.intersection((coord[0]-tolerance, coord[1]-tolerance,
                                              coord[0]+tolerance, coord[1]+tolerance)))

                found_existing = False
                for existing_id in nearby:
                    existing_coord = endpoints[existing_id]
                    if abs(existing_coord[0] - coord[0]) < tolerance and abs(existing_coord[1] - coord[1]) < tolerance:
                        seg_points.append(existing_id)
                        found_existing = True
                        break

                if not found_existing:
                    endpoints[point_id] = coord
                    idx.insert(point_id, (coord[0]-tolerance, coord[1]-tolerance,
                                        coord[0]+tolerance, coord[1]+tolerance))
                    seg_points.append(point_id)
                    point_id += 1

        segment_endpoints[seg_id] = seg_points

    print(f"Unique endpoints: {len(endpoints)}")

    # Build NetworkX graph
    print("Building graph...")
    G = nx.Graph()

    # Add all segments as nodes
    for seg_id in gdf.index:
        G.add_node(seg_id)

    # Add edges between segments that share endpoints
    for seg_id1, points1 in segment_endpoints.items():
        for seg_id2, points2 in segment_endpoints.items():
            if seg_id1 >= seg_id2:
                continue

            # Check if segments share any endpoints
            if set(points1) & set(points2):  # Intersection
                G.add_edge(seg_id1, seg_id2)

    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Find connected components
    print("Finding connected components...")
    components = list(nx.connected_components(G))

    print(f"\nConnectivity Results:")
    print(f"Connected components: {len(components)}")

    if len(components) == 1:
        print("✅ Motorways form a SINGLE connected network!")
    else:
        print("❌ Motorways are split into multiple networks")

        # Analyze components
        component_sizes = [(len(comp), comp) for comp in components]
        component_sizes.sort(reverse=True)

        for i, (size, comp) in enumerate(component_sizes[:10]):
            print(f"  Component {i+1}: {size} segments")

            # Show which motorways are in this component
            motorways_in_comp = set()
            for seg_idx in comp:
                road_num = gdf.iloc[seg_idx]['road_classification_number'] or 'Unknown'
                motorways_in_comp.add(road_num)

            motorway_list = sorted(list(motorways_in_comp))
            if len(motorway_list) <= 10:
                print(f"    Contains: {', '.join(motorway_list)}")
            else:
                print(f"    Contains: {', '.join(motorway_list[:10])}... (+{len(motorway_list)-10} more)")

if __name__ == "__main__":
    try:
        fast_motorway_connectivity()
    except ImportError as e:
        print(f"Missing required library: {e}")
        print("Install with: pip install networkx rtree")