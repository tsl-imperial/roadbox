"""
Main application module for RoadBox
Clean Flask app initialization and module coordination
"""

from flask import Flask
from flask_cors import CORS
from config import get_config
from api.routes import register_routes
from network.builder import network_builder


def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)

    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Enable CORS
    CORS(app)

    # Register API routes
    register_routes(app)

    # Print configuration info
    print(f"🔄 RoadBox initialized! Pathfinding tolerance: {app.config['PATHFINDING_TOLERANCE']} degrees")

    return app


def initialize_network():
    """Initialize the road network on startup"""
    print("🔧 Initializing MOTORWAY-ONLY pathfinding network...")
    try:
        network = network_builder.build_road_network()
        if network:
            print("✅ Pathfinding network ready!")
            return True
        else:
            print("❌ Failed to build pathfinding network")
            return False
    except Exception as e:
        print(f"❌ Error building pathfinding network: {e}")
        return False


# Create the app instance
app = create_app()


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════╗
║                    ROADBOX                       ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  Sandbox for exploring road network files        ║
║                                                  ║
║                                                  ║
║      Transport Systems & Logistics Laboratory    ║
║                                                  ║
║          Imperial College London                 ║
║                                                  ║
║      https://transport-systems.imperial.ac.uk    ║
║                                                  ║
║                                                  ║
║  Server will open at: http://localhost:5001      ║
║                                                  ║
╚══════════════════════════════════════════════════╝
    """)

    print("🚀 Starting RoadBox Server...")
    print("=" * 50)

    print("📊 Features:")
    print("  • FlatGeobuf backend (3x faster loading)")
    print("  • Viewport-based loading (only visible data)")
    print("  • Level-of-detail (zoom-based filtering)")
    print("  • Real-time pathfinding with NetworkX")
    print("  • Click to set start/end points")
    print()

    # Initialize network on startup
    initialize_network()
    print()

    print("🌐 Opening browser at http://localhost:5001")

    # Import webbrowser and timer for startup
    import webbrowser
    from threading import Timer

    def open_browser():
        webbrowser.open('http://localhost:5001')

    # Open browser after short delay
    Timer(2.0, open_browser).start()

    try:
        app.run(
            debug=app.config['DEBUG'],
            host=app.config['HOST'],
            port=app.config['PORT'],
            threaded=app.config['THREADED'],
            use_reloader=app.config['USE_RELOADER']
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")