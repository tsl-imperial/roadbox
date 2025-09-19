#!/usr/bin/env python3
"""
Clean motorways.fgb by keeping only the largest connected component
"""

import geopandas as gpd
import networkx as nx
from collections import defaultdict
import time

def build_network_from_gdf(gdf):
    """Build NetworkX graph from GeoDataFrame"""
    G = nx.Graph()

    # Track endpoints
    endpoint_to_segments = defaultdict(list)
    tolerance = 0.002  # ~200m tolerance

    for idx, row in gdf.iterrows():
        geom = row.geometry

        if geom.geom_type == 'LineString':
            coords = list(geom.coords)
            if len(coords) >= 2:
                start_point = coords[0]
                end_point = coords[-1]

                # Create node IDs
                start_node = f"node_{start_point[0]:.6f}_{start_point[1]:.6f}"
                end_node = f"node_{end_point[0]:.6f}_{end_point[1]:.6f}"

                # Add nodes
                G.add_node(start_node, lat=start_point[1], lon=start_point[0], segments=[idx])
                G.add_node(end_node, lat=end_point[1], lon=end_point[0], segments=[idx])

                # Add edge
                G.add_edge(start_node, end_node, segment_idx=idx)

                # Track for connections
                rounded_start = (round(start_point[0] / tolerance) * tolerance,
                               round(start_point[1] / tolerance) * tolerance)
                rounded_end = (round(end_point[0] / tolerance) * tolerance,
                             round(end_point[1] / tolerance) * tolerance)

                endpoint_to_segments[rounded_start].append((start_node, idx))
                endpoint_to_segments[rounded_end].append((end_node, idx))

    # Connect nearby endpoints
    connections_made = 0
    for endpoint_key, node_segments in endpoint_to_segments.items():
        if len(node_segments) > 1:
            # Connect all pairs in this group
            for i in range(len(node_segments)):
                for j in range(i + 1, len(node_segments)):
                    node1, seg1 = node_segments[i]
                    node2, seg2 = node_segments[j]

                    if not G.has_edge(node1, node2) and seg1 != seg2:
                        # Get actual coordinates
                        lat1, lon1 = G.nodes[node1]['lat'], G.nodes[node1]['lon']
                        lat2, lon2 = G.nodes[node2]['lat'], G.nodes[node2]['lon']

                        distance_deg = ((lat2-lat1)**2 + (lon2-lon1)**2)**0.5
                        distance_m = distance_deg * 111000

                        if distance_m <= tolerance * 111000:
                            G.add_edge(node1, node2, connection=True)
                            connections_made += 1

    print(f"Created {connections_made} connections between nearby segments")
    return G

def get_segments_in_component(G, component):
    """Get all segment indices in a connected component"""
    segments = set()
    for u, v, data in G.edges(data=True):
        if u in component or v in component:
            if 'segment_idx' in data:
                segments.add(data['segment_idx'])
    return segments

print("Loading motorways.fgb...")
gdf = gpd.read_file('motorways.fgb')
print(f"Loaded {len(gdf)} motorway segments")

# Build network
print("\nBuilding network graph...")
G = build_network_from_gdf(gdf)
print(f"Network has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

# Find connected components
print("\nFinding connected components...")
components = list(nx.connected_components(G))
print(f"Found {len(components)} connected components")

# Sort by size
components_sorted = sorted(components, key=len, reverse=True)
print("\nComponent sizes (nodes):")
for i, comp in enumerate(components_sorted[:10]):
    print(f"  Component {i+1}: {len(comp)} nodes")

# Get segments in largest component
largest_component = components_sorted[0]
segments_in_largest = get_segments_in_component(G, largest_component)

print(f"\nLargest component contains {len(segments_in_largest)} segments")

# Filter GeoDataFrame to keep only largest component
gdf_cleaned = gdf.iloc[list(segments_in_largest)].copy()

print(f"Removed {len(gdf) - len(gdf_cleaned)} disconnected segments")
print(f"Keeping {len(gdf_cleaned)} segments in main network")

# Save backup
print("\nBacking up original file...")
gdf.to_file('motorways_with_disconnected.fgb', driver='FlatGeobuf')

# Save cleaned version
print("Saving cleaned motorways...")
gdf_cleaned.to_file('motorways.fgb', driver='FlatGeobuf')

print("\n✅ Done! motorways.fgb now contains only the largest connected component")
print(f"   Original: {len(gdf)} segments")
print(f"   Cleaned: {len(gdf_cleaned)} segments")
print(f"   Removed: {len(gdf) - len(gdf_cleaned)} segments")