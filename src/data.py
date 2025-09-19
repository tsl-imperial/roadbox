"""
RoadBox Data Handler Module
Simple functions for data loading and filtering

This module provides:
- Efficient dataset loading with caching
- Spatial filtering for viewport-based loading
- Performance optimization for large datasets
- FlatGeobuf format support for fast I/O
"""

import os
import time
import geopandas as gpd
from shapely.geometry import box
from typing import Optional, Dict, List

# Module-level cache for datasets
_cached_datasets: Dict[str, gpd.GeoDataFrame] = {}

# File mapping for datasets
_file_mapping = {
    'motorways': 'data/motorways.fgb',
}


def load_dataset(dataset_name: str) -> Optional[gpd.GeoDataFrame]:
    """
    Load dataset with caching support

    Args:
        dataset_name: Name of the dataset to load (e.g., 'motorways')

    Returns:
        GeoDataFrame containing the spatial data, or None if loading fails
    """
    # Return cached version if available
    if dataset_name in _cached_datasets:
        return _cached_datasets[dataset_name]

    # Check if dataset name is valid
    if dataset_name not in _file_mapping:
        print(f"Unknown dataset: {dataset_name}")
        return None

    file_path = _file_mapping[dataset_name]

    # Check if file exists
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None

    print(f"Loading {file_path}...")
    start_time = time.time()

    try:
        # Load geospatial data using GeoPandas
        gdf = gpd.read_file(file_path)
        load_time = time.time() - start_time
        print(f"Loaded {len(gdf)} features in {load_time:.2f}s")

        # Cache the loaded dataset for future use
        _cached_datasets[dataset_name] = gdf
        return gdf

    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def get_cache_info() -> Dict[str, int]:
    """
    Get information about cached datasets

    Returns:
        Dictionary mapping dataset names to feature counts
    """
    return {name: len(gdf) for name, gdf in _cached_datasets.items()}


def filter_by_bbox(gdf: gpd.GeoDataFrame, bbox: Optional[List[float]]) -> gpd.GeoDataFrame:
    """
    Filter data by bounding box for efficient viewport loading

    This method performs spatial filtering to only include features that
    intersect with the current map viewport, significantly improving
    performance for large datasets.

    Args:
        gdf: GeoDataFrame containing spatial data
        bbox: Bounding box as [minx, miny, maxx, maxy] in map coordinates

    Returns:
        Filtered GeoDataFrame containing only features within the bbox
    """
    if not bbox or len(bbox) != 4:
        return gdf

    # Create bounding box geometry for spatial intersection
    minx, miny, maxx, maxy = bbox
    bbox_geom = box(minx, miny, maxx, maxy)

    # Use spatial index for efficient intersection testing
    mask = gdf.geometry.intersects(bbox_geom)
    filtered_gdf = gdf[mask]

    return filtered_gdf
