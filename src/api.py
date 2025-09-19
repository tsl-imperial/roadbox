"""
API routes module for RoadBox
Defines Flask endpoints and request handling
"""

import json
import time
from flask import jsonify, request, render_template
from . import data
from .network import find_route as calculate_route


def register_routes(app):
    """Register all API routes with the Flask app"""

    @app.route('/')
    def index():
        """Serve the main map page with pathfinding"""
        return render_template('index.html')

    @app.route('/api/data/<dataset>')
    def get_data(dataset):
        """API endpoint to get filtered road data"""
        start_time = time.time()

        # Load dataset
        gdf = data.load_dataset(dataset)
        if gdf is None:
            return jsonify({'error': 'Dataset not found'}), 404

        # Get query parameters
        bbox_str = request.args.get('bbox')

        # Parse bounding box
        bbox = None
        if bbox_str:
            try:
                bbox = [float(x) for x in bbox_str.split(',')]
            except:
                pass

        # Filter by bounding box (viewport)
        if bbox:
            filtered_gdf = data.filter_by_bbox(gdf, bbox)
        else:
            filtered_gdf = gdf

        # Convert to GeoJSON
        geojson = json.loads(filtered_gdf.to_json())

        processing_time = time.time() - start_time
        print(f"Served {len(filtered_gdf)} features in {processing_time:.3f}s")

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

        # Find route using pathfinder
        result = calculate_route(start_lat, start_lng, end_lat, end_lng)

        if 'error' in result:
            return jsonify(result), 400

        return jsonify(result)

    @app.route('/api/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'data_cache': data.get_cache_info(),
            'network': 'available'
        })