"""
RoadBox Network Graph Module
Simple functions for network building and pathfinding

This module provides:
- Graph theory applied to road networks
- Dijkstra's shortest path algorithm
- Hybrid NetworkX/iGraph approach for performance
- Geographic data processing for routing
"""

import time
import networkx as nx
import igraph as ig
import numpy as np
from collections import defaultdict
from typing import Tuple, Optional, Dict, Any, List
from shapely.geometry import Point
from . import data

# Module-level variables for network state
_road_network: Optional[nx.Graph] = None
_fast_graph: Optional[ig.Graph] = None
_node_mapping: Optional[Dict[str, Any]] = None


def build_road_network() -> Optional[nx.Graph]:
    """
    Build NetworkX graph from road data for pathfinding

    This method creates a mathematical graph representation of the road network:
    - Nodes represent road intersections and endpoints
    - Edges represent road segments connecting nodes
    - Weights represent travel cost (distance in this case)

    Returns:
        NetworkX Graph object ready for pathfinding algorithms
    """
    global _road_network, _fast_graph, _node_mapping

    if _road_network is not None:
        return _road_network

    print("Building road network for pathfinding...")
    start_time = time.time()

    # Load motorways dataset for pathfinding
    motorways = data.load_dataset('motorways')

    if motorways is None:
        print("Error: Could not load motorway data for network building")
        return None

    all_roads = motorways
    print(f"Using MOTORWAYS ONLY for pathfinding network ({len(all_roads)} segments)")

    # Create empty graph - this will hold our road network
    G = nx.Graph()

    # Process each road segment and add it to the graph
    for idx, row in all_roads.iterrows():
        geom = row.geometry
        road_type = row.get('road_classification_number', 'Unknown')

        if geom.geom_type == 'LineString':
            coords = list(geom.coords)
            if len(coords) >= 2:
                # Get start and end points of this road segment
                start_point = coords[0]  # (longitude, latitude)
                end_point = coords[-1]

                # Calculate segment length for routing weight
                # Convert from degrees to meters (approximate conversion)
                length = geom.length * 111000

                # Create unique identifiers for nodes
                start_node = f"node_{start_point[0]:.6f}_{start_point[1]:.6f}"
                end_node = f"node_{end_point[0]:.6f}_{end_point[1]:.6f}"

                # Add nodes to graph with their geographic coordinates
                G.add_node(start_node, lat=start_point[1], lon=start_point[0])
                G.add_node(end_node, lat=end_point[1], lon=end_point[0])

                # Add edge between nodes with routing weight (distance)
                G.add_edge(start_node, end_node,
                          weight=length,
                          length=length,
                          road_type=road_type,
                          segment_id=f"seg_{idx}",
                          geometry=coords)

    build_time = time.time() - start_time
    initial_nodes = G.number_of_nodes()
    initial_edges = G.number_of_edges()
    print(f"Initial network: {initial_nodes} nodes, {initial_edges} edges in {build_time:.2f}s")

    # Connect road segments that are close to each other (intersections)
    _connect_adjacent_segments(G)

    # Keep only the largest connected component for pathfinding
    G = _get_largest_component(G)

    # Create a faster version using igraph for routing calculations
    _build_igraph(G)

    _road_network = G
    return G


def _connect_adjacent_segments(G: nx.Graph):
    """
    Connect adjacent motorway segments to form a connected network

    Problem: Road data often has gaps where segments don't connect properly.
    Solution: Find road endpoints that are very close and connect them.

    This is crucial for pathfinding - without connections, routes can't cross
    between different road segments.
    """
    print("Connecting adjacent motorway segments...")
    gap_start_time = time.time()

    # Group nearby endpoints for efficient connection finding
    endpoint_to_segments = defaultdict(list)
    tolerance = 0.002  # ~200m tolerance - roads this close should connect

    # Find all road endpoints and group them by location
    for node in G.nodes():
        node_data = G.nodes[node]
        lat, lon = node_data['lat'], node_data['lon']

        # Round coordinates to create spatial groups
        # This groups nearby endpoints together for efficient processing
        rounded_lat = round(lat / tolerance) * tolerance
        rounded_lon = round(lon / tolerance) * tolerance
        endpoint_key = (rounded_lat, rounded_lon)

        endpoint_to_segments[endpoint_key].append(node)

    # Connect nodes that are very close to each other
    connections_made = 0
    for endpoint_key, nodes in endpoint_to_segments.items():
        if len(nodes) > 1:
            # Multiple road endpoints in the same area - likely an intersection
            # Connect all pairs to ensure full connectivity
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    node1, node2 = nodes[i], nodes[j]

                    if not G.has_edge(node1, node2):
                        # Calculate actual distance between the two points
                        node1_data = G.nodes[node1]
                        node2_data = G.nodes[node2]

                        lat1, lon1 = node1_data['lat'], node1_data['lon']
                        lat2, lon2 = node2_data['lat'], node2_data['lon']

                        # Simple Euclidean distance in degrees, then convert to meters
                        distance_deg = ((lat2-lat1)**2 + (lon2-lon1)**2)**0.5
                        distance_m = distance_deg * 111000

                        # Only connect if within tolerance distance
                        if distance_m <= tolerance * 111000:
                            G.add_edge(node1, node2,
                                      weight=distance_m,
                                      length=distance_m,
                                      road_type='MOTORWAY_CONNECTION',
                                      segment_id=f'connection_{connections_made}')
                            connections_made += 1

    gap_time = time.time() - gap_start_time
    print(f"Connectivity complete in {gap_time:.2f}s")
    print(f"Created {connections_made} connections between road segments")


def _get_largest_component(G: nx.Graph) -> nx.Graph:
    """
    Keep only the largest connected component of the road network

    Why this matters:
    - Real road networks often have disconnected parts (islands, separate regions)
    - Pathfinding algorithms can only find routes within connected components
    - We keep the largest component to ensure most roads are accessible

    This is a standard preprocessing step in network analysis.
    """
    print("Finding largest connected component...")
    components = list(nx.connected_components(G))
    print(f"Found {len(components)} connected components")

    if len(components) > 1:
        # Sort components by number of nodes (largest first)
        components_sorted = sorted(components, key=len, reverse=True)
        largest_component = components_sorted[0]

        print(f"Component sizes: {[len(c) for c in components_sorted[:5]]}...")
        print(f"Keeping largest component with {len(largest_component)} nodes")

        # Create a new graph containing only the largest component
        G = G.subgraph(largest_component).copy()

        print(f"Final network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    else:
        print("Network is fully connected - no isolated components!")

    return G


def _build_igraph(G: nx.Graph):
    """
    Convert NetworkX graph to igraph for ultra-fast routing

    Why use both libraries?
    - NetworkX: Pure Python, full graph analysis capabilities
    - iGraph: C implementation, 10-100x faster for large networks
    """
    global _fast_graph, _node_mapping

    print("Converting to igraph for ultra-fast routing...")
    igraph_start = time.time()

    # Create node mapping between NetworkX and iGraph indices
    node_list = list(G.nodes())
    node_to_index = {node: i for i, node in enumerate(node_list)}

    # Build edge list for igraph
    edge_list = []
    edge_weights = []

    for u, v, data in G.edges(data=True):
        edge_list.append((node_to_index[u], node_to_index[v]))
        weight = data.get('weight', data.get('length', 1.0))
        edge_weights.append(weight)

    # Create igraph instance
    ig_graph = ig.Graph(n=len(node_list), edges=edge_list, directed=False)
    ig_graph.es['weight'] = edge_weights

    # Store node data in igraph format
    for i, node in enumerate(node_list):
        node_data = G.nodes[node]
        ig_graph.vs[i]['name'] = node
        ig_graph.vs[i]['lat'] = node_data['lat']
        ig_graph.vs[i]['lon'] = node_data['lon']

    igraph_time = time.time() - igraph_start
    print(f"Igraph conversion complete in {igraph_time:.2f}s - READY FOR LIGHTNING-FAST ROUTING!")

    # Store both representations
    _fast_graph = ig_graph
    _node_mapping = {'to_index': node_to_index, 'to_node': node_list}


def find_nearest_node(graph: nx.Graph, lat: float, lon: float,
                     max_distance: Optional[float] = None) -> Tuple[Optional[str], float]:
    """
    Find the nearest node in the road network to a given geographic point

    This is a key step in routing: when a user clicks on the map, we need to
    find the closest road junction or endpoint to start/end the route.

    Args:
        graph: Road network graph
        lat, lon: Geographic coordinates of the target point
        max_distance: Maximum search radius (degrees)

    Returns:
        Tuple of (node_id, distance) or (None, inf) if no node found
    """
    tolerance = 0.5  # Default tolerance
    if max_distance is None:
        max_distance = tolerance

    print(f"Finding nearest node within {max_distance*111:.0f}km of {lat:.4f}, {lon:.4f}")

    min_distance = float('inf')
    nearest_node = None
    target_point = Point(lon, lat)

    # Search through all nodes to find the closest one
    # Note: This is O(n) complexity - could be optimized with spatial indexing for large networks
    for node in graph.nodes():
        node_data = graph.nodes[node]
        node_point = Point(node_data['lon'], node_data['lat'])
        distance = target_point.distance(node_point)

        if distance < min_distance and distance <= max_distance:
            min_distance = distance
            nearest_node = node

    return nearest_node, min_distance


def find_route(start_lat: float, start_lng: float,
               end_lat: float, end_lng: float) -> Dict[str, Any]:
    """
    Find the shortest route between two geographic points

    This is the main pathfinding function that:
    1. Finds the nearest road nodes to the start/end points
    2. Uses Dijkstra's algorithm to find the shortest path
    3. Returns the route with coordinates and metadata

    Args:
        start_lat, start_lng: Starting point coordinates
        end_lat, end_lng: Destination point coordinates

    Returns:
        Dictionary with route information or error message
    """
    # Ensure we have a road network to work with
    graph = build_road_network()
    if graph is None:
        return {'error': 'Could not build road network'}

    print(f"Finding route from {start_lat:.4f},{start_lng:.4f} to {end_lat:.4f},{end_lng:.4f}")

    try:
        # Step 1: Find the nearest road nodes to our start and end points
        start_node, start_dist = find_nearest_node(graph, start_lat, start_lng)
        end_node, end_dist = find_nearest_node(graph, end_lat, end_lng)

        if start_node is None or end_node is None:
            return {'error': 'Could not find nearby roads within search radius'}

        print(f"Start node: {start_node} (distance: {start_dist:.6f}°)")
        print(f"End node: {end_node} (distance: {end_dist:.6f}°)")

        # Step 2: Calculate shortest path using available algorithm
        # Try fast igraph implementation first, fallback to NetworkX
        if _fast_graph and _node_mapping:
            path = _find_route_igraph(start_node, end_node, start_lng, start_lat, end_lng, end_lat)
        else:
            path = _find_route_networkx(graph, start_node, end_node, start_lng, start_lat, end_lng, end_lat)

        return path

    except nx.NetworkXNoPath:
        return {'error': 'No route found - points may be on disconnected road segments'}
    except Exception as e:
        print(f"Pathfinding error: {e}")
        return {'error': f'Pathfinding failed: {str(e)}'}


def _find_route_igraph(start_node: str, end_node: str,
                      start_lng: float, start_lat: float,
                      end_lng: float, end_lat: float) -> Dict[str, Any]:
    """
    Find route using igraph library (optimized for speed)

    igraph is a specialized graph library that implements Dijkstra's algorithm
    very efficiently, optimized for large networks and high-performance routing.
    """
    # Convert node names to indices for igraph
    start_idx = _node_mapping['to_index'][start_node]
    end_idx = _node_mapping['to_index'][end_node]

    # Run Dijkstra's shortest path algorithm
    path_indices = _fast_graph.get_shortest_paths(
        start_idx, end_idx, weights='weight', output="vpath")[0]

    # Convert indices back to node names
    path = [_node_mapping['to_node'][idx] for idx in path_indices]

    return _build_route_response(_road_network, path,
                                start_lng, start_lat, end_lng, end_lat)


def _find_route_networkx(graph: nx.Graph, start_node: str, end_node: str,
                       start_lng: float, start_lat: float,
                       end_lng: float, end_lat: float) -> Dict[str, Any]:
    """
    Find route using NetworkX library (fallback implementation)

    NetworkX provides a clean Python implementation of shortest path algorithms
    with full access to intermediate results and algorithm customization.
    """
    # Use NetworkX's implementation of Dijkstra's algorithm
    path = nx.shortest_path(graph, start_node, end_node, weight='weight')
    return _build_route_response(graph, path, start_lng, start_lat, end_lng, end_lat)


def _build_route_response(graph: nx.Graph, path: List[str],
                        start_lng: float, start_lat: float,
                        end_lng: float, end_lat: float) -> Dict[str, Any]:
    """
    Build route response from the calculated path

    This converts the abstract graph path (list of node IDs) into
    geographic coordinates that can be displayed on a map.
    """
    # Calculate total distance and collect route information
    total_distance = 0
    roads_used = set()
    route_coords = []

    # Add start point to route
    route_coords.append([start_lng, start_lat])

    # Process each segment of the path
    for i in range(len(path) - 1):
        current_node = path[i]
        next_node = path[i + 1]

        # Get edge data for this segment
        edge_data = graph.edges[current_node, next_node]
        total_distance += edge_data['length']
        roads_used.add(edge_data['road_type'])

        # Add detailed geometry if available, otherwise use node coordinates
        if 'geometry' in edge_data and edge_data['geometry']:
            # Use the full road geometry for accurate route display
            geometry = edge_data['geometry']
            current_lat = graph.nodes[current_node]['lat']
            current_lon = graph.nodes[current_node]['lon']

            if len(geometry) > 0:
                first_point = geometry[0]
                last_point = geometry[-1]

                # Check which direction matches our path direction
                dist_to_first = ((first_point[0] - current_lon)**2 + (first_point[1] - current_lat)**2)**0.5
                dist_to_last = ((last_point[0] - current_lon)**2 + (last_point[1] - current_lat)**2)**0.5

                if dist_to_last < dist_to_first:
                    # Reverse the geometry to match our travel direction
                    geometry = list(reversed(geometry))

                # Add all intermediate points (skip first if not first segment to avoid duplicates)
                start_idx = 1 if i > 0 else 0
                for point in geometry[start_idx:]:
                    route_coords.append([point[0], point[1]])
        else:
            # Fallback to just node coordinates
            node_data = graph.nodes[next_node]
            route_coords.append([node_data['lon'], node_data['lat']])

    # Add end point to route
    route_coords.append([end_lng, end_lat])

    result = {
        'route': {
            'type': 'LineString',
            'coordinates': route_coords
        },
        'distance': total_distance,
        'roads': sorted(list(roads_used)),
        'nodes': len(path)
    }

    print(f"Route found: {total_distance/1000:.1f}km via {len(path)} nodes")
    return result


def get_network_info() -> Dict[str, Any]:
    """Get information about the current network for debugging"""
    if _road_network is None:
        return {"status": "No network built"}

    return {
        "nodes": _road_network.number_of_nodes(),
        "edges": _road_network.number_of_edges(),
        "has_igraph": _fast_graph is not None
    }


