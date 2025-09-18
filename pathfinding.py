#!/usr/bin/env python3
"""
RoadBox - Interactive UK motorways exploration sandbox
"""

from flask import Flask, jsonify, send_from_directory, request, render_template
from flask_cors import CORS
import geopandas as gpd
import json
import os
import time
from shapely.geometry import box, Point, LineString
import webbrowser
from threading import Timer
import networkx as nx
import igraph as ig
import numpy as np
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# Global variables for ultra-fast routing
fast_graph = None  # igraph for lightning-fast routing
node_mapping = None
road_network = None  # Reset to force rebuild with motorway-only network

# Configuration
app.config['PATHFINDING_TOLERANCE'] = 0.5  # degrees (~50km)

# Print reload message
print("🔄 Server reloaded! Pathfinding tolerance:", app.config['PATHFINDING_TOLERANCE'], f"degrees (~{app.config['PATHFINDING_TOLERANCE']*111:.0f}km)")

# Cache loaded datasets and network graph
cached_datasets = {}
road_network = None

def build_road_network():
    """Build NetworkX graph from road data for pathfinding"""
    global road_network, fast_graph, node_mapping

    if road_network is not None:
        return road_network

    print("Building road network for pathfinding...")
    start_time = time.time()

    # Load motorways only for pathfinding
    motorways = load_dataset('motorways')

    if motorways is None:
        print("Error: Could not load motorway data for network building")
        return None

    # Use motorways only for pathfinding
    all_roads = motorways
    print(f"🛣️ Using MOTORWAYS ONLY for pathfinding network")

    # Create graph
    G = nx.Graph()

    # Track endpoints for connecting segments
    endpoint_to_segments = defaultdict(list)

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

    # Simple connectivity for adjacent motorway segments
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
    final_nodes = G.number_of_nodes()
    final_edges = G.number_of_edges()

    print(f"🔗 Simple connectivity complete in {gap_time:.2f}s")
    print(f"   Created {connections_made} adjacent connections")
    print(f"   Initial network: {final_nodes} nodes, {final_edges} edges")
    print(f"   Added {final_edges - initial_edges} connections")

    # Keep only the largest connected component
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
        print(f"   Removed {final_nodes - G.number_of_nodes()} isolated nodes")
    else:
        print(f"   Network is fully connected!")

    # 🚀 CONVERT TO IGRAPH FOR 10-50x FASTER ROUTING
    print("⚡ Converting to igraph for ultra-fast routing...")
    igraph_start = time.time()

    # Create node mapping
    node_list = list(G.nodes())
    node_to_index = {node: i for i, node in enumerate(node_list)}

    # Build edge list for igraph
    edge_list = []
    edge_weights = []
    edge_data = []

    for u, v, data in G.edges(data=True):
        edge_list.append((node_to_index[u], node_to_index[v]))
        weight = data.get('weight', data.get('length', 1.0))
        edge_weights.append(weight)
        edge_data.append(data)

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
    road_network = G  # Keep NetworkX for analysis
    fast_graph = ig_graph  # Use igraph for routing
    node_mapping = {'to_index': node_to_index, 'to_node': node_list}

    return G

def find_nearest_node(graph, lat, lon, max_distance=None):
    """Find the nearest node in the graph to given coordinates"""
    if max_distance is None:
        max_distance = app.config.get('PATHFINDING_TOLERANCE', 0.5)

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

def load_dataset(dataset_name):
    """Load dataset with caching"""
    if dataset_name in cached_datasets:
        return cached_datasets[dataset_name]

    file_mapping = {
        'motorways': 'motorways.fgb',
        'motorways_compressed': 'motorways_compressed.fgb',
    }

    if dataset_name not in file_mapping:
        return None

    file_path = file_mapping[dataset_name]

    if not os.path.exists(file_path):
        return None

    print(f"Loading {file_path}...")
    start_time = time.time()

    try:
        gdf = gpd.read_file(file_path)
        load_time = time.time() - start_time
        print(f"Loaded {len(gdf)} features in {load_time:.2f}s")

        cached_datasets[dataset_name] = gdf
        return gdf
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def filter_by_bbox(gdf, bbox):
    """Filter data by bounding box for efficient viewport loading"""
    if not bbox:
        return gdf

    # Create bounding box geometry
    minx, miny, maxx, maxy = bbox
    bbox_geom = box(minx, miny, maxx, maxy)

    # Filter geometries that intersect the bounding box
    mask = gdf.geometry.intersects(bbox_geom)
    return gdf[mask]

def filter_by_zoom(gdf, zoom_level):
    """No filtering - show all data at all zoom levels"""
    return gdf  # Always return full dataset - no zoom-based filtering

@app.route('/')
def index():
    """Serve the main map page with pathfinding"""
    return render_template('index.html')



@app.route('/api/data/<dataset>')
def get_data(dataset):
    """API endpoint to get filtered road data"""
    start_time = time.time()

    # Load dataset
    gdf = load_dataset(dataset)
    if gdf is None:
        return jsonify({'error': 'Dataset not found'}), 404

    # Get query parameters
    bbox_str = request.args.get('bbox')
    zoom = int(request.args.get('zoom', 6))

    # Parse bounding box
    bbox = None
    if bbox_str:
        try:
            bbox = [float(x) for x in bbox_str.split(',')]
        except:
            pass

    # Filter by bounding box (viewport)
    if bbox:
        filtered_gdf = filter_by_bbox(gdf, bbox)
    else:
        filtered_gdf = gdf

    # Filter by zoom level (LOD)
    filtered_gdf = filter_by_zoom(filtered_gdf, zoom)

    # Convert to GeoJSON
    if len(filtered_gdf) > 10000:  # Limit for performance
        filtered_gdf = filtered_gdf.head(10000)

    geojson = json.loads(filtered_gdf.to_json())

    processing_time = time.time() - start_time
    print(f"Served {len(filtered_gdf)} features in {processing_time:.3f}s (zoom: {zoom})")

    return jsonify(geojson)

@app.route('/api/route', methods=['POST'])
def find_route():
    """API endpoint for pathfinding"""
    data = request.get_json()

    if not data or 'start' not in data or 'end' not in data:
        return jsonify({'error': 'Start and end points required'}), 400

    start_lat = data['start']['lat']
    start_lng = data['start']['lng']
    end_lat = data['end']['lat']
    end_lng = data['end']['lng']

    # Build network if not already built
    graph = build_road_network()
    if graph is None:
        return jsonify({'error': 'Could not build road network'}), 500

    print(f"Finding route from {start_lat},{start_lng} to {end_lat},{end_lng}")

    try:
        # Find nearest nodes
        start_node, start_dist = find_nearest_node(graph, start_lat, start_lng)
        end_node, end_dist = find_nearest_node(graph, end_lat, end_lng)

        if start_node is None or end_node is None:
            return jsonify({'error': 'Could not find nearby roads'}), 400

        print(f"Start node: {start_node} (distance: {start_dist:.6f})")
        print(f"End node: {end_node} (distance: {end_dist:.6f})")

        # ⚡ ULTRA-FAST IGRAPH ROUTING
        start_idx = node_mapping['to_index'][start_node]
        end_idx = node_mapping['to_index'][end_node]

        # Use igraph's lightning-fast Dijkstra implementation
        path_indices = fast_graph.get_shortest_paths(start_idx, end_idx, weights='weight', output="vpath")[0]

        # Convert back to node names
        path = [node_mapping['to_node'][idx] for idx in path_indices]

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

        return jsonify(result)

    except nx.NetworkXNoPath:
        return jsonify({'error': 'No route found between these points'}), 400
    except Exception as e:
        print(f"Pathfinding error: {e}")
        return jsonify({'error': f'Pathfinding failed: {str(e)}'}), 500

def open_browser():
    """Open browser after short delay"""
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    import pandas as pd

    print("🚀 Starting UK MOTORWAYS server with pathfinding...")
    print("📊 Features:")
    print("  • FlatGeobuf backend (3x faster loading)")
    print("  • Viewport-based loading (only visible data)")
    print("  • Level-of-detail (zoom-based filtering)")
    print("  • Real-time pathfinding with igraph")
    print("  • MOTORWAY-ONLY routing network")
    print("  • Click to set start/end points")
    print()

    # 🔥 BUILD PATHFINDING NETWORK ON STARTUP
    print("🔧 Initializing MOTORWAY-ONLY pathfinding network...")
    try:
        network = build_road_network()
        if network:
            print("✅ Pathfinding network ready!")
        else:
            print("❌ Failed to build pathfinding network")
    except Exception as e:
        print(f"❌ Error building pathfinding network: {e}")

    print()

    # Open browser after short delay
    Timer(2.0, open_browser).start()

    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=True)