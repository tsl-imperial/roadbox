#!/usr/bin/env python3
"""
RoadBox - Interactive UK motorways exploration sandbox
Run this to start the RoadBox server
"""

import os
import sys
import yaml
from pathlib import Path

def check_requirements():
    """Check that all required files and dependencies exist"""

    # Check required data files
    required_files = [
        'data/motorways.fgb'
    ]

    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        print("❌ Missing required data files:")
        for file in missing_files:
            print(f"   - {file}")
        return False


    return True

def load_config():
    """Load configuration from YAML file"""
    with open('config.yml', 'r') as f:
        return yaml.safe_load(f)

def start_server():
    """Start the roads server"""

    if not check_requirements():
        sys.exit(1)

    # Load configuration
    config = load_config()

    print("Starting RoadBox Server...")
    print("="*50)

    # Import and run the RoadBox app
    from src.app import app
    import webbrowser
    from threading import Timer

    def open_browser():
        webbrowser.open(f'http://localhost:{config["port"]}')

    print()
    print(f"🌐 Opening browser at http://localhost:{config['port']}")

    # Open browser after short delay
    Timer(2.0, open_browser).start()

    try:
        app.run(
            debug=config['debug'],
            host=config['host'],
            port=config['port'],
            threaded=config['threaded'],
            use_reloader=config['use_reloader']
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    # Load config to show correct port in banner
    config = load_config()

    print(f"""
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
║  Server will open at: http://localhost:{config['port']:<4}      ║
║                                                  ║
╚══════════════════════════════════════════════════╝
    """)

    start_server()