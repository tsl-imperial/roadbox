#!/usr/bin/env python3
"""
RoadBox - Interactive UK motorways exploration sandbox
Run this to start the RoadBox server
"""

import os
import sys
from pathlib import Path

def check_requirements():
    """Check that all required files and dependencies exist"""

    # Check required data files
    required_files = [
        'motorways.fgb'
    ]

    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        print("❌ Missing required data files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n💡 Run the data conversion scripts first:")
        print("   python3 convert_to_flatgeobuf.py")
        return False

    # Check Python dependencies
    try:
        import flask
        import flask_cors
        import geopandas
        import networkx
        import shapely
    except ImportError as e:
        print(f"❌ Missing Python dependency: {e}")
        print("\n💡 Install with: pip3 install flask flask-cors geopandas networkx shapely flatgeobuf")
        return False

    return True

def start_server():
    """Start the roads server"""

    if not check_requirements():
        sys.exit(1)

    print("🚀 Starting RoadBox Server...")
    print("="*50)

    # Import and run the RoadBox app
    from app import app
    import webbrowser
    from threading import Timer

    def open_browser():
        webbrowser.open('http://localhost:5001')

    print("📊 Features:")
    print("  • FlatGeobuf backend (3x faster loading)")
    print("  • Viewport-based loading (only visible data)")
    print("  • Level-of-detail (zoom-based filtering)")
    print("  • Real-time pathfinding with NetworkX")
    print("  • Click to set start/end points")
    print()
    print("🌐 Opening browser at http://localhost:5001")

    # Open browser after short delay
    Timer(2.0, open_browser).start()

    try:
        app.run(
            debug=True,  # Enable debug for auto-reload
            host='0.0.0.0',
            port=5001,
            threaded=True,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
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
║              Imperial College London             ║
║                                                  ║
║      https://transport-systems.imperial.ac.uk    ║
║                                                  ║
║                                                  ║
║  Server will open at: http://localhost:5001      ║
║                                                  ║
╚══════════════════════════════════════════════════╝
    """)

    start_server()