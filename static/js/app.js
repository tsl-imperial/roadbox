// Restore map state from localStorage or use defaults
const savedCenter = JSON.parse(localStorage.getItem('mapCenter') || '[54.5, -2.0]');
const savedZoom = parseInt(localStorage.getItem('mapZoom') || '6');
const map = L.map('map').setView(savedCenter, savedZoom);

// Save map state on move/zoom
map.on('moveend zoomend', function() {
    localStorage.setItem('mapCenter', JSON.stringify([map.getCenter().lat, map.getCenter().lng]));
    localStorage.setItem('mapZoom', map.getZoom().toString());
});

L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap contributors © CARTO | Road data: OS OpenRoads © Crown copyright'
}).addTo(map);

// Add scale control (ruler)
L.control.scale({
    position: 'bottomright',
    metric: true,
    imperial: true,
    updateWhenIdle: false
}).addTo(map);

const motorwayLayer = L.layerGroup().addTo(map);
const routeLayer = L.layerGroup().addTo(map);

let mode = null;
let startPoint = null;
let endPoint = null;
let startMarker = null;
let endMarker = null;

// Measuring tool variables
let measuring = false;
let measurePoints = [];
let measureLine = null;
let measureMarkers = [];
let totalDistance = 0;

// Simple marker icons
const startIcon = L.divIcon({
    html: '<div style="background: #00ff00; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
});

const endIcon = L.divIcon({
    html: '<div style="background: #ff0000; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
});

const measureIcon = L.divIcon({
    html: '<div style="background: #ffa500; width: 16px; height: 16px; border-radius: 50%; border: 2px solid white;"></div>',
    iconSize: [16, 16],
    iconAnchor: [8, 8]
});

function setMode(newMode) {
    mode = newMode;

    // Remove active class from both buttons
    document.getElementById('set-start').classList.remove('active');
    document.getElementById('set-end').classList.remove('active');

    // Add active class to the selected button
    if (mode === 'start') {
        document.getElementById('set-start').classList.add('active');
    } else if (mode === 'end') {
        document.getElementById('set-end').classList.add('active');
    }

    map.getContainer().style.cursor = 'crosshair';
}

map.on('click', function(e) {
    if (mode === 'start') {
        startPoint = e.latlng;
        if (startMarker) map.removeLayer(startMarker);
        startMarker = L.marker([e.latlng.lat, e.latlng.lng], {
            icon: startIcon,
            draggable: true
        }).addTo(map);

        // Add drag event listener
        startMarker.on('dragend', function(e) {
            startPoint = e.target.getLatLng();
            if (startPoint && endPoint) {
                findRoute();
            }
        });
        mode = null;
        // Remove active classes when mode is cleared
        document.getElementById('set-start').classList.remove('active');
        document.getElementById('set-end').classList.remove('active');
        map.getContainer().style.cursor = '';
        updateRouteButton();
    } else if (mode === 'end') {
        endPoint = e.latlng;
        if (endMarker) map.removeLayer(endMarker);
        endMarker = L.marker([e.latlng.lat, e.latlng.lng], {
            icon: endIcon,
            draggable: true
        }).addTo(map);

        // Add drag event listener
        endMarker.on('dragend', function(e) {
            endPoint = e.target.getLatLng();
            if (startPoint && endPoint) {
                findRoute();
            }
        });
        mode = null;
        // Remove active classes when mode is cleared
        document.getElementById('set-start').classList.remove('active');
        document.getElementById('set-end').classList.remove('active');
        map.getContainer().style.cursor = '';
        updateRouteButton();
    } else if (measuring) {
        addMeasurePoint(e.latlng);
    }
});

function updateRouteButton() {
    const canRoute = startPoint && endPoint;
    document.getElementById('find-route').disabled = !canRoute;
    document.getElementById('set-start').style.background = '#007cba';
    document.getElementById('set-end').style.background = '#007cba';
}

async function findRoute() {
    if (!startPoint || !endPoint) return;

    document.getElementById('route-info').innerHTML = 'Finding route...';

    try {
        const response = await fetch('/api/route', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start: { lat: startPoint.lat, lng: startPoint.lng },
                end: { lat: endPoint.lat, lng: endPoint.lng }
            })
        });

        const result = await response.json();

        if (result.error) {
            document.getElementById('route-info').innerHTML = 'Error: ' + result.error;
            // Disable clear button since there's no route
            document.getElementById('clear-route').disabled = true;
            return;
        }

        // Clear existing route
        routeLayer.clearLayers();

        // Add route to map
        const routeLine = L.polyline(result.route.coordinates.map(c => [c[1], c[0]]), {
            color: '#ffff00',
            weight: 5,
            opacity: 0.8
        }).addTo(routeLayer);

        // Update info
        const distance = (result.distance / 1000).toFixed(1);
        const roads = result.roads.slice(0, 5).join(', ');
        document.getElementById('route-info').innerHTML =
            '<strong>Distance:</strong> ' + distance + ' km<br>' +
            '<strong>Roads:</strong> ' + roads + (result.roads.length > 5 ? '...' : '');

        // Enable clear button now that we have a route
        document.getElementById('clear-route').disabled = false;

        // Fit map to route
        map.fitBounds(routeLine.getBounds(), { padding: [20, 20] });

    } catch (error) {
        document.getElementById('route-info').innerHTML = 'Error: ' + error.message;
        // Disable clear button since there's no route
        document.getElementById('clear-route').disabled = true;
    }
}

function clearRoute() {
    routeLayer.clearLayers();
    if (startMarker) map.removeLayer(startMarker);
    if (endMarker) map.removeLayer(endMarker);
    startPoint = null;
    endPoint = null;
    startMarker = null;
    endMarker = null;
    document.getElementById('route-info').innerHTML = '';

    // Disable clear button since there's no route
    document.getElementById('clear-route').disabled = true;

    updateRouteButton();
}

// Measuring tool functions
function startMeasuring() {
    measuring = !measuring;
    const button = document.getElementById('start-measure');

    if (measuring) {
        button.innerHTML = 'Stop Measuring';
        button.style.background = '#ff6b6b';
        map.getContainer().style.cursor = 'crosshair';
        document.getElementById('measurement-info').innerHTML = 'Click on map to start measuring...';
    } else {
        button.innerHTML = 'Start Measuring';
        button.style.background = '#007cba';
        map.getContainer().style.cursor = '';
        if (measurePoints.length > 0) {
            document.getElementById('measurement-info').innerHTML = `Total distance: ${totalDistance.toFixed(2)} km`;
        }
    }
}

function addMeasurePoint(latlng) {
    measurePoints.push(latlng);

    // Add marker
    const marker = L.marker([latlng.lat, latlng.lng], {icon: measureIcon}).addTo(map);
    measureMarkers.push(marker);

    if (measurePoints.length > 1) {
        // Calculate distance from previous point
        const prevPoint = measurePoints[measurePoints.length - 2];
        const distance = map.distance(prevPoint, latlng) / 1000; // Convert to km
        totalDistance += distance;

        // Update or create line
        if (measureLine) {
            map.removeLayer(measureLine);
        }

        measureLine = L.polyline(measurePoints.map(p => [p.lat, p.lng]), {
            color: '#ffa500',
            weight: 3,
            opacity: 0.8,
            dashArray: '10, 5'
        }).addTo(map);

        document.getElementById('measurement-info').innerHTML =
            `Points: ${measurePoints.length} | Total: ${totalDistance.toFixed(2)} km | Last segment: ${distance.toFixed(2)} km`;
    } else {
        document.getElementById('measurement-info').innerHTML = 'Click next point to measure distance...';
    }
}

function clearMeasurements() {
    // Clear markers
    measureMarkers.forEach(marker => map.removeLayer(marker));
    measureMarkers = [];

    // Clear line
    if (measureLine) {
        map.removeLayer(measureLine);
        measureLine = null;
    }

    // Reset variables
    measurePoints = [];
    totalDistance = 0;

    // Update display
    document.getElementById('measurement-info').innerHTML = '';

    // Reset measuring state
    if (measuring) {
        measuring = false;
        document.getElementById('start-measure').innerHTML = 'Start Measuring';
        document.getElementById('start-measure').style.background = '#007cba';
        map.getContainer().style.cursor = '';
    }
}

async function loadData(dataset, layer, color) {
    const bounds = map.getBounds();
    const zoom = map.getZoom();

    const bbox = bounds.getWest() + ',' + bounds.getSouth() + ',' + bounds.getEast() + ',' + bounds.getNorth();
    const url = '/api/data/' + dataset + '?bbox=' + bbox + '&zoom=' + zoom;

    const startTime = performance.now();

    try {
        const response = await fetch(url);
        const data = await response.json();

        const loadTime = performance.now() - startTime;
        document.getElementById('feature-count').textContent = 'Visible features: ' + data.features.length + ' elements';

        layer.clearLayers();

        L.geoJSON(data, {
            style: { color: color, weight: 3, opacity: 0.8 },
            onEachFeature: function(feature, leafletLayer) {
                const props = feature.properties;
                const popup =
                    '<strong>' + (props.road_classification_number || 'Unknown') + '</strong><br>' +
                    '<strong>Name:</strong> ' + (props.name_1 || 'Unnamed') + '<br>' +
                    '<strong>Length:</strong> ' + (props.length ? (props.length/1000).toFixed(2) + ' km' : 'Unknown');
                leafletLayer.bindPopup(popup);
            }
        }).addTo(layer);

    } catch (error) {
        console.error('Error loading ' + dataset + ':', error);
    }
}

function updateLayers() {
    if (map.hasLayer(motorwayLayer)) {
        loadData('motorways', motorwayLayer, '#ff6b6b');
    }
}


map.on('moveend zoomend', updateLayers);

document.getElementById('motorways-toggle').addEventListener('change', function(e) {
    if (e.target.checked) {
        map.addLayer(motorwayLayer);
        loadData('motorways', motorwayLayer, '#ff6b6b');
    } else {
        map.removeLayer(motorwayLayer);
    }
    // Save layer state to localStorage
    localStorage.setItem('motorways-visible', e.target.checked);
});



// Restore layer states from localStorage
const motorwaysVisible = localStorage.getItem('motorways-visible');

if (motorwaysVisible === 'true') {
    document.getElementById('motorways-toggle').checked = true;
    map.addLayer(motorwayLayer);
} else if (motorwaysVisible === 'false') {
    document.getElementById('motorways-toggle').checked = false;
}

updateLayers();