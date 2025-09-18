"""
Pathfinding module for RoadBox
Handles route calculations and navigation algorithms
"""

import networkx as nx
from shapely.geometry import Point
from typing import Tuple, Optional, Dict, Any, List
from network.builder import network_builder


class Pathfinder:
    """Handles pathfinding operations on road networks"""

    def __init__(self, tolerance: float = 0.5):
        """
        Initialize pathfinder

        Args:
            tolerance: Maximum distance in degrees to search for nearest nodes
        """
        self.tolerance = tolerance

    def find_nearest_node(self, graph: nx.Graph, lat: float, lon: float,
                         max_distance: Optional[float] = None) -> Tuple[Optional[str], float]:
        """Find the nearest node in the graph to given coordinates"""
        if max_distance is None:
            max_distance = self.tolerance

        print(f"🔍 Finding nearest node within {max_distance} degrees (~{max_distance*111:.0f}km) of {lat:.4f}, {lon:.4f}")

        min_distance = float('inf')
        nearest_node = None

        target_point = Point(lon, lat)

        for node in graph.nodes():
            node_data = graph.nodes[node]
            node_point = Point(node_data['lon'], node_data['lat'])
            distance = target_point.distance(node_point)

            if distance < min_distance and distance <= max_distance:
                min_distance = distance
                nearest_node = node

        return nearest_node, min_distance

    def find_route(self, start_lat: float, start_lng: float,
                   end_lat: float, end_lng: float) -> Dict[str, Any]:
        """
        Find route between two points

        Returns:
            Dictionary containing route data or error information
        """
        # Build network if not already built
        graph = network_builder.build_road_network()
        if graph is None:
            return {'error': 'Could not build road network'}

        print(f"Finding route from {start_lat},{start_lng} to {end_lat},{end_lng}")

        try:
            # Find nearest nodes
            start_node, start_dist = self.find_nearest_node(graph, start_lat, start_lng)
            end_node, end_dist = self.find_nearest_node(graph, end_lat, end_lng)

            if start_node is None or end_node is None:
                return {'error': 'Could not find nearby roads'}

            print(f"Start node: {start_node} (distance: {start_dist:.6f})")
            print(f"End node: {end_node} (distance: {end_dist:.6f})")

            # Use igraph's lightning-fast Dijkstra implementation
            if network_builder.fast_graph and network_builder.node_mapping:
                path = self._find_route_igraph(start_node, end_node, start_lng, start_lat, end_lng, end_lat)
            else:
                path = self._find_route_networkx(graph, start_node, end_node, start_lng, start_lat, end_lng, end_lat)

            return path

        except nx.NetworkXNoPath:
            return {'error': 'No route found between these points'}
        except Exception as e:
            print(f"Pathfinding error: {e}")
            return {'error': f'Pathfinding failed: {str(e)}'}

    def _find_route_igraph(self, start_node: str, end_node: str,
                          start_lng: float, start_lat: float,
                          end_lng: float, end_lat: float) -> Dict[str, Any]:
        """Find route using igraph for speed"""
        start_idx = network_builder.node_mapping['to_index'][start_node]
        end_idx = network_builder.node_mapping['to_index'][end_node]

        # Use igraph's lightning-fast Dijkstra implementation
        path_indices = network_builder.fast_graph.get_shortest_paths(
            start_idx, end_idx, weights='weight', output="vpath")[0]

        # Convert back to node names
        path = [network_builder.node_mapping['to_node'][idx] for idx in path_indices]

        return self._build_route_response(network_builder.road_network, path,
                                        start_lng, start_lat, end_lng, end_lat)

    def _find_route_networkx(self, graph: nx.Graph, start_node: str, end_node: str,
                           start_lng: float, start_lat: float,
                           end_lng: float, end_lat: float) -> Dict[str, Any]:
        """Find route using NetworkX as fallback"""
        path = nx.shortest_path(graph, start_node, end_node, weight='weight')
        return self._build_route_response(graph, path, start_lng, start_lat, end_lng, end_lat)

    def _build_route_response(self, graph: nx.Graph, path: List[str],
                            start_lng: float, start_lat: float,
                            end_lng: float, end_lat: float) -> Dict[str, Any]:
        """Build route response from path"""
        # Calculate total distance
        total_distance = 0
        roads_used = set()
        route_coords = []

        # Add start point
        route_coords.append([start_lng, start_lat])

        # Add path coordinates using full road geometry
        for i in range(len(path) - 1):
            current_node = path[i]
            next_node = path[i + 1]

            # Get edge data
            edge_data = graph.edges[current_node, next_node]
            total_distance += edge_data['length']
            roads_used.add(edge_data['road_type'])

            # Use full geometry if available, otherwise fall back to endpoints
            if 'geometry' in edge_data and edge_data['geometry']:
                # Add all points from the road geometry
                geometry = edge_data['geometry']
                # Check if we need to reverse the geometry
                current_lat = graph.nodes[current_node]['lat']
                current_lon = graph.nodes[current_node]['lon']

                if len(geometry) > 0:
                    first_point = geometry[0]
                    last_point = geometry[-1]

                    # Check which direction matches our path
                    dist_to_first = ((first_point[0] - current_lon)**2 + (first_point[1] - current_lat)**2)**0.5
                    dist_to_last = ((last_point[0] - current_lon)**2 + (last_point[1] - current_lat)**2)**0.5

                    if dist_to_last < dist_to_first:
                        # Reverse the geometry
                        geometry = list(reversed(geometry))

                    # Add all intermediate points (skip first if not first segment to avoid duplicates)
                    start_idx = 1 if i > 0 else 0
                    for point in geometry[start_idx:]:
                        route_coords.append([point[0], point[1]])
            else:
                # Fallback to just node coordinates
                node_data = graph.nodes[next_node]
                route_coords.append([node_data['lon'], node_data['lat']])

        # Add end point
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


# Global instance for backwards compatibility
pathfinder = Pathfinder()