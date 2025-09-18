# RoadBox

A high-performance sandbox for exploring UK motorways with interactive mapping and pathfinding capabilities.

## Quick Start

### Prerequisites

- Python 3.7+
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/roadbox.git
cd roadbox
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. The motorways.fgb file is included in the repository

4. Run the server:
```bash
python3 start.py
```

The server will start and automatically open your browser at `http://localhost:5001`

## Usage

### Navigation
- **Pan**: Click and drag the map
- **Zoom**: Use scroll wheel or zoom controls
- **Scale**: Check the scale control in bottom-right corner

### Pathfinding
1. Click **"Set Start Point"** then click on the map to place green marker
2. Click **"Set End Point"** then click on the map to place red marker
3. Click **"Find Route"** to calculate the optimal path
4. The yellow line shows your route with distance and roads used
5. Click **"Clear Route"** to reset

### Measuring Tool
1. Click **"Start Measuring"** to begin
2. Click multiple points on the map to measure distances
3. Orange markers and dashed lines show your measurements
4. View total distance and segment lengths
5. Click **"Clear All"** to remove measurements

## Technical Details

### Architecture

- **Backend**: Flask server with NetworkX/iGraph pathfinding
- **Frontend**: Leaflet.js with dark CartoDB basemap
- **Data Format**: FlatGeobuf for optimal performance
- **Routing Algorithm**: Dijkstra's algorithm with motorway optimization


### Data Source

The motorways.fgb file (included in this repository) contains UK motorway network data derived from Ordnance Survey OpenRoads dataset.

**Original Data Source**: [OS OpenRoads](https://osdatahub.os.uk/downloads/open/OpenRoads)

The file includes:
- All UK motorway segments as LineString geometries
- Properties: `road_classification_number`, `name_1`, `length`
- Complete M25 orbital with Dartford Crossing connection

## Development

### Adding New Features

The codebase is modular and extensible:

- **Routing algorithms**: Modify `build_road_network()` in `pathfinding.py`
- **Map styling**: Edit `static/css/style.css`
- **UI components**: Update `templates/index.html` and `static/js/app.js`

### API Endpoints

- `GET /` - Main application page
- `GET /api/data/<dataset>` - Get road data for viewport
- `POST /api/route` - Calculate route between two points

## License

### Software License
MIT License - see LICENSE file for details

### Data License
The motorways data is derived from OS OpenRoads and is licensed under the [Open Government Licence v3.0](http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

Contains OS data © Crown copyright and database right 2024.

## Acknowledgments

- Road network data from [Ordnance Survey OpenRoads](https://osdatahub.os.uk/downloads/open/OpenRoads)
- Map tiles from CartoDB/OpenStreetMap
- Routing powered by NetworkX and iGraph