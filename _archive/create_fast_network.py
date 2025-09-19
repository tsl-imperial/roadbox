#!/usr/bin/env python3
"""
Create a much smaller, faster network for web pathfinding
"""

import geopandas as gpd
import pandas as pd
import json
import networkx as nx
from shapely.geometry import Point

def create_minimal_network():
    """Create a minimal network with only major intersections"""
    print("Creating minimal pathfinding network...")

    # Load the merged roads
    roads = gpd.read_file('uk_major_roads_merged.geojson')
    print(f"Total roads: {len(roads):,}")

    # Filter for only major roads to reduce complexity
    major_roads = roads[
        (roads['road_classification'] == 'Motorway') |
        (roads['road_classification_number'].str.match(r'^[AM]\d{1,2}$', na=False))
    ].copy()

    print(f"Major roads: {len(major_roads):,}")

    # Create NetworkX graph for easier processing
    G = nx.Graph()

    # Add nodes and edges
    node_id = 0
    coord_to_node = {}

    for idx, row in major_roads.iterrows():
        if row.geometry.geom_type == 'LineString':
            coords = list(row.geometry.coords)

            # Only use start and end points to simplify
            start_coord = coords[0]
            end_coord = coords[-1]

            # Add start node
            if start_coord not in coord_to_node:
                coord_to_node[start_coord] = node_id
                G.add_node(node_id, lon=start_coord[0], lat=start_coord[1])
                node_id += 1

            # Add end node
            if end_coord not in coord_to_node:
                coord_to_node[end_coord] = node_id
                G.add_node(node_id, lon=end_coord[0], lat=end_coord[1])
                node_id += 1

            # Add edge
            start_node_id = coord_to_node[start_coord]
            end_node_id = coord_to_node[end_coord]

            length = row.get('length', 1000)  # Default length
            weight = length / (1 if row['road_classification'] == 'Motorway' else 2)  # Motorways are faster

            G.add_edge(start_node_id, end_node_id,
                      length=length,
                      weight=weight,
                      road_class=row['road_classification'],
                      road_number=row.get('road_classification_number', ''))

    print(f"Initial graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Keep only the largest connected component
    largest_cc = max(nx.connected_components(G), key=len)
    G = G.subgraph(largest_cc).copy()

    print(f"Largest component: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Further reduce by keeping only nodes with degree > 1 or important endpoints
    nodes_to_keep = set()
    for node in G.nodes():
        degree = G.degree[node]
        if degree > 2:  # Intersections
            nodes_to_keep.add(node)
        elif degree == 1:  # Endpoints - keep some
            nodes_to_keep.add(node)

    # If still too large, sample nodes
    if len(nodes_to_keep) > 2000:
        import random
        nodes_list = list(nodes_to_keep)
        random.shuffle(nodes_list)
        nodes_to_keep = set(nodes_list[:2000])

    # Create simplified graph
    G_simple = G.subgraph(nodes_to_keep).copy()

    # Remove isolated nodes
    isolated = list(nx.isolates(G_simple))
    G_simple.remove_nodes_from(isolated)

    print(f"Simplified graph: {G_simple.number_of_nodes()} nodes, {G_simple.number_of_edges()} edges")

    return G_simple

def save_fast_network(G):
    """Save network in format optimized for web pathfinding"""

    # Convert to simple format
    nodes = []
    edges = []

    # Remap node IDs to be sequential
    node_mapping = {}
    for i, node_id in enumerate(G.nodes()):
        node_mapping[node_id] = i
        node_data = G.nodes[node_id]
        nodes.append({
            'id': i,
            'lat': node_data['lat'],
            'lon': node_data['lon']
        })

    for edge in G.edges(data=True):
        start_id = node_mapping[edge[0]]
        end_id = node_mapping[edge[1]]
        edge_data = edge[2]

        edges.append({
            'start': start_id,
            'end': end_id,
            'weight': edge_data['weight'],
            'length': edge_data['length']
        })

    # Create adjacency list for faster pathfinding
    adjacency = {}
    for i in range(len(nodes)):
        adjacency[i] = []

    for edge in edges:
        adjacency[edge['start']].append({
            'node': edge['end'],
            'weight': edge['weight'],
            'length': edge['length']
        })
        adjacency[edge['end']].append({
            'node': edge['start'],
            'weight': edge['weight'],
            'length': edge['length']
        })

    network_data = {
        'nodes': nodes,
        'edges': edges,
        'adjacency': adjacency,
        'metadata': {
            'node_count': len(nodes),
            'edge_count': len(edges),
            'optimized': True
        }
    }

    # Save compact JSON
    with open('uk_road_network_fast.json', 'w') as f:
        json.dump(network_data, f, separators=(',', ':'))

    print(f"Saved fast network: {len(nodes)} nodes, {len(edges)} edges")

    # Create even smaller network for testing
    if len(nodes) > 500:
        # Sample 500 random nodes for ultra-fast testing
        import random
        sample_nodes = random.sample(range(len(nodes)), 500)
        sample_node_set = set(sample_nodes)

        small_nodes = [nodes[i] for i in sample_nodes]
        small_edges = []
        small_adjacency = {}

        # Remap again
        small_node_mapping = {old_id: new_id for new_id, old_id in enumerate(sample_nodes)}

        for i in range(len(small_nodes)):
            small_adjacency[i] = []

        for edge in edges:
            if edge['start'] in sample_node_set and edge['end'] in sample_node_set:
                new_start = small_node_mapping[edge['start']]
                new_end = small_node_mapping[edge['end']]

                small_edges.append({
                    'start': new_start,
                    'end': new_end,
                    'weight': edge['weight'],
                    'length': edge['length']
                })

                small_adjacency[new_start].append({
                    'node': new_end,
                    'weight': edge['weight'],
                    'length': edge['length']
                })
                small_adjacency[new_end].append({
                    'node': new_start,
                    'weight': edge['weight'],
                    'length': edge['length']
                })

        small_network = {
            'nodes': small_nodes,
            'edges': small_edges,
            'adjacency': small_adjacency,
            'metadata': {
                'node_count': len(small_nodes),
                'edge_count': len(small_edges),
                'ultra_fast': True
            }
        }

        with open('uk_road_network_ultrafast.json', 'w') as f:
            json.dump(small_network, f, separators=(',', ':'))

        print(f"Saved ultra-fast network: {len(small_nodes)} nodes, {len(small_edges)} edges")

def main():
    print("Creating fast pathfinding network")
    print("=" * 40)

    G = create_minimal_network()
    save_fast_network(G)

    print("\nFast network files created:")
    print("  - uk_road_network_fast.json")
    print("  - uk_road_network_ultrafast.json")

if __name__ == "__main__":
    main()