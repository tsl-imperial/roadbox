"""
Data filtering module for RoadBox
Handles spatial and zoom-based filtering operations
"""

import geopandas as gpd
from shapely.geometry import box
from typing import List, Optional


class DataFilter:
    """Handles filtering operations on geospatial data"""

    @staticmethod
    def filter_by_bbox(gdf: gpd.GeoDataFrame, bbox: Optional[List[float]]) -> gpd.GeoDataFrame:
        """Filter data by bounding box for efficient viewport loading"""
        if not bbox or len(bbox) != 4:
            return gdf

        # Create bounding box geometry
        minx, miny, maxx, maxy = bbox
        bbox_geom = box(minx, miny, maxx, maxy)

        # Filter geometries that intersect the bounding box
        mask = gdf.geometry.intersects(bbox_geom)
        return gdf[mask]

    @staticmethod
    def filter_by_zoom(gdf: gpd.GeoDataFrame, zoom_level: int) -> gpd.GeoDataFrame:
        """Filter by zoom level (Level of Detail)"""
        # Currently no filtering - show all data at all zoom levels
        # This can be enhanced in the future for performance optimization
        return gdf

    @staticmethod
    def limit_features(gdf: gpd.GeoDataFrame, max_features: int = 10000) -> gpd.GeoDataFrame:
        """Limit number of features for performance"""
        if len(gdf) > max_features:
            return gdf.head(max_features)
        return gdf


# Global instance for convenience
data_filter = DataFilter()