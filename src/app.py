"""
RoadBox - Road Network Analysis Platform
Main application module for road network analysis and pathfinding
"""

import os
import yaml
from flask import Flask
from flask_cors import CORS
from .api import register_routes
from .network import build_road_network


def load_config():
    """Load configuration from YAML file"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yml')

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def create_app():
    """
    Create and configure Flask application

    Loads configuration from config.yml and sets up the application.
    """
    # Load configuration from YAML
    config = load_config()

    # Configure Flask to find templates and static files in parent directory
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    # Apply configuration to Flask app
    app.config.update(config)

    # Enable CORS (Cross-Origin Resource Sharing) for API access
    # This allows the frontend JavaScript to communicate with our backend
    CORS(app)

    # Register all API endpoints
    register_routes(app)

    # Print startup information for debugging
    tolerance_km = config['pathfinding_tolerance'] * 111
    print(f"RoadBox initialized! Pathfinding search radius: {tolerance_km:.0f}km")

    return app


def initialize_network():
    """
    Initialize the road network graph for pathfinding

    This creates two representations of the road network:
    1. NetworkX graph (readable, good for analysis)
    2. iGraph version (optimized for fast pathfinding with Dijkstra's algorithm)

    The dual approach provides both algorithmic transparency and
    high performance for interactive use.

    Returns:
        True if network built successfully, False otherwise
    """
    print("Initializing road network for pathfinding...")
    try:
        network = build_road_network()
        if network:
            nodes = network.number_of_nodes()
            edges = network.number_of_edges()
            print(f"✅ Network ready! {nodes} junctions, {edges} road segments")
            print("   Both NetworkX (analysis) and iGraph (performance) versions created")
            return True
        else:
            print("❌ Failed to build pathfinding network")
            return False
    except Exception as e:
        print(f"❌ Error building pathfinding network: {e}")
        return False


# Create the Flask application instance using the factory pattern
app = create_app()


if __name__ == '__main__':
    # Initialize network on startup
    initialize_network()

    # Run the app directly (for development)
    app.run(
        debug=app.config['debug'],
        host=app.config['host'],
        port=app.config['port'],
        threaded=app.config['threaded'],
        use_reloader=app.config['use_reloader']
    )