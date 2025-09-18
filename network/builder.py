"""
Network builder module for RoadBox
Handles road network graph construction and connectivity
"""

import time
import networkx as nx
import igraph as ig
import numpy as np
from collections import defaultdict
from typing import Tuple, Optional, Dict, Any
from data.loader import data_loader


class NetworkBuilder:
    """Builds and manages road network graphs"""

    def __init__(self):
        self.road_network: Optional[nx.Graph] = None
        self.fast_graph: Optional[ig.Graph] = None
        self.node_mapping: Optional[Dict[str, Any]] = None

    def build_road_network(self) -> Optional[nx.Graph]:
        """Build NetworkX graph from road data for pathfinding"""
        if self.road_network is not None:
            return self.road_network

        print("Building road network for pathfinding...")
        start_time = time.time()

        # Load motorways only for pathfinding
        motorways = data_loader.load_dataset('motorways')

        if motorways is None:
            print("Error: Could not load motorway data for network building")
            return None

        # Use motorways only for pathfinding
        all_roads = motorways
        print(f"🛣️ Using MOTORWAYS ONLY for pathfinding network")

        # Create graph
        G = nx.Graph()

        print(f"Processing {len(all_roads)} road segments...")

        for idx, row in all_roads.iterrows():
            geom = row.geometry
            road_type = row.get('road_classification_number', 'Unknown')

            if geom.geom_type == 'LineString':
                coords = list(geom.coords)
                if len(coords) >= 2:
                    start_point = coords[0]
                    end_point = coords[-1]

                    # Calculate segment length (for routing weight)
                    length = geom.length * 111000  # Convert degrees to meters (approximate)

                    # Add segment to graph
                    segment_id = f"seg_{idx}"
                    start_node = f"node_{start_point[0]:.6f}_{start_point[1]:.6f}"
                    end_node = f"node_{end_point[0]:.6f}_{end_point[1]:.6f}"

                    # Add nodes with coordinates
                    G.add_node(start_node, lat=start_point[1], lon=start_point[0])
                    G.add_node(end_node, lat=end_point[1], lon=end_point[0])

                    # Add edge with weight and road info
                    weight = length  # Use actual length as weight for motorways

                    G.add_edge(start_node, end_node,
                              weight=weight,
                              length=length,
                              road_type=road_type,
                              segment_id=segment_id,
                              geometry=coords)  # Store full geometry for route display

        build_time = time.time() - start_time
        initial_nodes = G.number_of_nodes()
        initial_edges = G.number_of_edges()
        print(f"Initial network: {initial_nodes} nodes, {initial_edges} edges in {build_time:.2f}s")

        # Connect adjacent segments
        self._connect_adjacent_segments(G)

        # Keep only the largest connected component
        G = self._get_largest_component(G)

        # Convert to igraph for fast routing
        self._build_igraph(G)

        self.road_network = G
        return G

    def _connect_adjacent_segments(self, G: nx.Graph):
        """Connect adjacent motorway segments"""
        print("🔗 Connecting adjacent motorway segments...")
        gap_start_time = time.time()

        # Track endpoints for connecting segments
        endpoint_to_segments = defaultdict(list)
        tolerance = 0.002  # ~200m tolerance for connecting roads

        # Find endpoints and group nearby ones
        for node in G.nodes():
            node_data = G.nodes[node]
            lat, lon = node_data['lat'], node_data['lon']

            # Round coordinates to create groups of nearby endpoints
            rounded_lat = round(lat / tolerance) * tolerance
            rounded_lon = round(lon / tolerance) * tolerance
            endpoint_key = (rounded_lat, rounded_lon)

            endpoint_to_segments[endpoint_key].append(node)

        # Connect nodes that are very close to each other (likely intersections)
        connections_made = 0
        for endpoint_key, nodes in endpoint_to_segments.items():
            if len(nodes) > 1:
                # Connect all pairs of nodes in this group
                for i in range(len(nodes)):
                    for j in range(i + 1, len(nodes)):
                        node1, node2 = nodes[i], nodes[j]

                        if not G.has_edge(node1, node2):
                            # Calculate distance between nodes
                            node1_data = G.nodes[node1]
                            node2_data = G.nodes[node2]

                            lat1, lon1 = node1_data['lat'], node1_data['lon']
                            lat2, lon2 = node2_data['lat'], node2_data['lon']

                            distance_deg = ((lat2-lat1)**2 + (lon2-lon1)**2)**0.5
                            distance_m = distance_deg * 111000

                            # Only connect if very close (within tolerance)
                            if distance_m <= tolerance * 111000:
                                G.add_edge(node1, node2,
                                          weight=distance_m,
                                          length=distance_m,
                                          road_type='MOTORWAY_CONNECTION',
                                          segment_id=f'connection_{connections_made}')
                                connections_made += 1

        gap_time = time.time() - gap_start_time
        print(f"🔗 Simple connectivity complete in {gap_time:.2f}s")
        print(f"   Created {connections_made} adjacent connections")

    def _get_largest_component(self, G: nx.Graph) -> nx.Graph:
        """Keep only the largest connected component"""
        print("🌐 Finding largest connected component...")
        components = list(nx.connected_components(G))
        print(f"   Found {len(components)} connected components")

        if len(components) > 1:
            # Sort components by size
            components_sorted = sorted(components, key=len, reverse=True)
            largest_component = components_sorted[0]

            # Print component sizes
            print(f"   Component sizes: {[len(c) for c in components_sorted[:5]]}...")
            print(f"   Keeping largest component with {len(largest_component)} nodes")

            # Create subgraph with only the largest component
            G = G.subgraph(largest_component).copy()

            print(f"   Final network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        else:
            print(f"   Network is fully connected!")

        return G

    def _build_igraph(self, G: nx.Graph):
        """Convert NetworkX graph to igraph for ultra-fast routing"""
        print("⚡ Converting to igraph for ultra-fast routing...")
        igraph_start = time.time()

        # Create node mapping
        node_list = list(G.nodes())
        node_to_index = {node: i for i, node in enumerate(node_list)}

        # Build edge list for igraph
        edge_list = []
        edge_weights = []

        for u, v, data in G.edges(data=True):
            edge_list.append((node_to_index[u], node_to_index[v]))
            weight = data.get('weight', data.get('length', 1.0))
            edge_weights.append(weight)

        # Create igraph
        ig_graph = ig.Graph(n=len(node_list), edges=edge_list, directed=False)
        ig_graph.es['weight'] = edge_weights

        # Store node data
        for i, node in enumerate(node_list):
            node_data = G.nodes[node]
            ig_graph.vs[i]['name'] = node
            ig_graph.vs[i]['lat'] = node_data['lat']
            ig_graph.vs[i]['lon'] = node_data['lon']

        igraph_time = time.time() - igraph_start
        print(f"⚡ Igraph conversion complete in {igraph_time:.2f}s - READY FOR LIGHTNING-FAST ROUTING!")

        # Store both for different purposes
        self.fast_graph = ig_graph
        self.node_mapping = {'to_index': node_to_index, 'to_node': node_list}

    def get_network_info(self) -> Dict[str, Any]:
        """Get information about the current network"""
        if self.road_network is None:
            return {"status": "No network built"}

        return {
            "nodes": self.road_network.number_of_nodes(),
            "edges": self.road_network.number_of_edges(),
            "has_igraph": self.fast_graph is not None
        }


# Global instance for backwards compatibility
network_builder = NetworkBuilder()