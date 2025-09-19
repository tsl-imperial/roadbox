#!/usr/bin/env python3
"""
Create merged dataset and network topology for pathfinding
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import json
from shapely.geometry import Point, LineString
from scipy.spatial import cKDTree
import networkx as nx

def merge_road_datasets():
    """Merge motorways and A roads into single dataset"""
    print("Merging motorways and A roads...")

    # Load both datasets
    motorways = gpd.read_file('motorways_wgs84.geojson')
    a_roads = gpd.read_file('major_a_roads_wgs84.geojson')

    print(f"Motorways: {len(motorways):,}")
    print(f"A roads: {len(a_roads):,}")

    # Combine datasets
    combined = pd.concat([motorways, a_roads], ignore_index=True)
    combined = gpd.GeoDataFrame(combined)

    # Add unique ID for each road segment
    combined['segment_id'] = range(len(combined))

    # Add road priority for pathfinding (lower = higher priority)
    combined['priority'] = combined['road_classification'].map({
        'Motorway': 1,
        'A Road': 2
    })

    print(f"Combined roads: {len(combined):,}")

    return combined

def create_network_topology(roads_gdf):
    """Create network topology for pathfinding"""
    print("Creating network topology...")

    nodes = []
    edges = []
    node_id = 0

    # Extract all coordinate points and create nodes
    coord_to_node = {}

    for idx, row in roads_gdf.iterrows():
        if row.geometry.geom_type == 'LineString':
            coords = list(row.geometry.coords)

            # Get start and end node IDs
            start_coord = coords[0]
            end_coord = coords[-1]

            # Create nodes if they don't exist
            if start_coord not in coord_to_node:
                coord_to_node[start_coord] = node_id
                nodes.append({
                    'node_id': node_id,
                    'lon': start_coord[0],
                    'lat': start_coord[1]
                })
                node_id += 1

            if end_coord not in coord_to_node:
                coord_to_node[end_coord] = node_id
                nodes.append({
                    'node_id': node_id,
                    'lon': end_coord[0],
                    'lat': end_coord[1]
                })
                node_id += 1

            # Create edge
            start_node_id = coord_to_node[start_coord]
            end_node_id = coord_to_node[end_coord]

            # Calculate length in meters (approximate)
            length = row.get('length', row.geometry.length * 111000)  # rough conversion

            edges.append({
                'edge_id': idx,
                'start_node': start_node_id,
                'end_node': end_node_id,
                'length': length,
                'road_class': row['road_classification'],
                'road_number': row.get('road_classification_number', ''),
                'priority': row['priority'],
                'segment_id': row['segment_id']
            })

    print(f"Created {len(nodes):,} nodes and {len(edges):,} edges")

    return nodes, edges

def save_pathfinding_data(roads_gdf, nodes, edges):
    """Save all data needed for pathfinding"""

    # Save merged roads
    roads_gdf.to_file('uk_major_roads_merged.geojson', driver='GeoJSON')
    print("Saved uk_major_roads_merged.geojson")

    # Save network data as JSON for web use
    network_data = {
        'nodes': nodes,
        'edges': edges,
        'metadata': {
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'road_classes': list(roads_gdf['road_classification'].unique())
        }
    }

    with open('uk_road_network.json', 'w') as f:
        json.dump(network_data, f, separators=(',', ':'))  # Compact JSON

    print("Saved uk_road_network.json")

    # Create simplified version for faster web loading
    # Only include major nodes (intersections with multiple connections)
    node_connections = {}
    for edge in edges:
        start_node = edge['start_node']
        end_node = edge['end_node']

        if start_node not in node_connections:
            node_connections[start_node] = 0
        if end_node not in node_connections:
            node_connections[end_node] = 0

        node_connections[start_node] += 1
        node_connections[end_node] += 1

    # Keep nodes with multiple connections (intersections) and their direct neighbors
    important_nodes = set()
    for node_id, connections in node_connections.items():
        if connections > 2:  # Intersection
            important_nodes.add(node_id)

    # Add nodes connected to important nodes
    for edge in edges:
        if edge['start_node'] in important_nodes or edge['end_node'] in important_nodes:
            important_nodes.add(edge['start_node'])
            important_nodes.add(edge['end_node'])

    # Create simplified network
    simplified_nodes = [node for node in nodes if node['node_id'] in important_nodes]
    simplified_edges = [edge for edge in edges
                       if edge['start_node'] in important_nodes and edge['end_node'] in important_nodes]

    simplified_network = {
        'nodes': simplified_nodes,
        'edges': simplified_edges,
        'metadata': {
            'total_nodes': len(simplified_nodes),
            'total_edges': len(simplified_edges),
            'is_simplified': True
        }
    }

    with open('uk_road_network_simplified.json', 'w') as f:
        json.dump(simplified_network, f, separators=(',', ':'))

    print(f"Saved simplified network: {len(simplified_nodes):,} nodes, {len(simplified_edges):,} edges")

def main():
    print("Creating pathfinding dataset for UK major roads")
    print("=" * 50)

    # Step 1: Merge datasets
    combined_roads = merge_road_datasets()

    # Step 2: Create network topology
    nodes, edges = create_network_topology(combined_roads)

    # Step 3: Save all data
    save_pathfinding_data(combined_roads, nodes, edges)

    print("\nPathfinding dataset creation complete!")
    print("Files created:")
    print("  - uk_major_roads_merged.geojson (visual data)")
    print("  - uk_road_network.json (full network)")
    print("  - uk_road_network_simplified.json (fast network)")

if __name__ == "__main__":
    main()