#!/usr/bin/env python3
"""
Create a connected network by merging sequential road segments
"""

import geopandas as gpd
import pandas as pd
import json
import networkx as nx
from collections import defaultdict

def create_connected_network():
    """Create connected network by merging sequential road segments"""
    print("Creating connected network with merged segments...")

    # Load the original simplified network
    with open('uk_road_network_simplified.json', 'r') as f:
        original_network = json.load(f)

    print(f"Original network: {len(original_network['nodes'])} nodes, {len(original_network['edges'])} edges")

    # Build NetworkX graph
    G = nx.Graph()

    # Add nodes
    for node in original_network['nodes']:
        G.add_node(node['node_id'], lat=node['lat'], lon=node['lon'])

    # Add edges
    for edge in original_network['edges']:
        G.add_edge(edge['start_node'], edge['end_node'],
                  length=edge['length'],
                  road_class=edge.get('road_class', 'A Road'),
                  road_number=edge.get('road_number', ''))

    print(f"NetworkX graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Find nodes that can be merged (degree 2 nodes that just pass through)
    def can_merge_node(node):
        """Check if a node can be merged (degree 2 and same road type)"""
        if G.degree[node] != 2:
            return False

        neighbors = list(G.neighbors(node))
        edge1 = G[node][neighbors[0]]
        edge2 = G[node][neighbors[1]]

        # Only merge if same road class
        return edge1.get('road_class') == edge2.get('road_class')

    # Iteratively merge nodes
    merged_count = 0
    max_iterations = 10000  # Prevent infinite loops

    for iteration in range(max_iterations):
        nodes_to_merge = [node for node in G.nodes() if can_merge_node(node)]

        if not nodes_to_merge:
            break

        for node in nodes_to_merge:
            if node in G and can_merge_node(node):  # Double check since graph changes
                neighbors = list(G.neighbors(node))
                if len(neighbors) == 2:
                    n1, n2 = neighbors

                    # Get edge data
                    edge1_data = G[node][n1]
                    edge2_data = G[node][n2]

                    # Calculate combined length
                    combined_length = edge1_data['length'] + edge2_data['length']

                    # Remove old edges and node
                    G.remove_node(node)

                    # Add new direct edge
                    G.add_edge(n1, n2,
                              length=combined_length,
                              road_class=edge1_data['road_class'],
                              road_number=edge1_data.get('road_number', ''))

                    merged_count += 1

        print(f"Iteration {iteration + 1}: Merged {len(nodes_to_merge)} nodes")

        if len(nodes_to_merge) < 100:  # Stop when few nodes left to merge
            break

    print(f"Total nodes merged: {merged_count}")
    print(f"Final graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Ensure we have the largest connected component
    if not nx.is_connected(G):
        largest_cc = max(nx.connected_components(G), key=len)
        G = G.subgraph(largest_cc).copy()
        print(f"Largest connected component: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    return G

def save_connected_network(G):
    """Save the connected network"""

    # Convert to list format with sequential IDs
    nodes = []
    edges = []
    node_mapping = {}

    # Create sequential node IDs
    for i, node_id in enumerate(G.nodes()):
        node_mapping[node_id] = i
        node_data = G.nodes[node_id]
        nodes.append({
            'id': i,
            'lat': node_data['lat'],
            'lon': node_data['lon']
        })

    # Create edges with new IDs
    for edge in G.edges(data=True):
        start_id = node_mapping[edge[0]]
        end_id = node_mapping[edge[1]]
        edge_data = edge[2]

        # Weight favors motorways
        road_class = edge_data.get('road_class', 'A Road')
        length = edge_data['length']
        weight = length / (1 if road_class == 'Motorway' else 1.5)

        edges.append({
            'start': start_id,
            'end': end_id,
            'weight': weight,
            'length': length,
            'road_class': road_class,
            'road_number': edge_data.get('road_number', '')
        })

    # Create adjacency list for fast pathfinding
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
            'connected': True,
            'simplified': True
        }
    }

    # Save the network
    with open('uk_road_network_connected.json', 'w') as f:
        json.dump(network_data, f, separators=(',', ':'))

    print(f"Saved connected network: {len(nodes)} nodes, {len(edges)} edges")

    # Verify connectivity by checking if we can reach all nodes from node 0
    visited = set()
    stack = [0]

    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)

        for neighbor in adjacency[current]:
            if neighbor['node'] not in visited:
                stack.append(neighbor['node'])

    connectivity_ratio = len(visited) / len(nodes)
    print(f"Connectivity check: {len(visited)}/{len(nodes)} nodes reachable ({connectivity_ratio:.1%})")

    return len(nodes), len(edges), connectivity_ratio

def main():
    print("Creating connected pathfinding network")
    print("=" * 45)

    G = create_connected_network()
    node_count, edge_count, connectivity = save_connected_network(G)

    print(f"\nConnected network created successfully!")
    print(f"  Nodes: {node_count:,}")
    print(f"  Edges: {edge_count:,}")
    print(f"  Connectivity: {connectivity:.1%}")
    print(f"  File: uk_road_network_connected.json")

if __name__ == "__main__":
    main()