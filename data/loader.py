"""
Data loader module for RoadBox
Handles dataset loading, caching, and file operations
"""

import os
import time
import geopandas as gpd
from typing import Optional, Dict


class DataLoader:
    """Handles loading and caching of geospatial datasets"""

    def __init__(self):
        self.cached_datasets: Dict[str, gpd.GeoDataFrame] = {}
        self.file_mapping = {
            'motorways': 'motorways.fgb',
            'motorways_compressed': 'motorways_compressed.fgb',
        }

    def load_dataset(self, dataset_name: str) -> Optional[gpd.GeoDataFrame]:
        """Load dataset with caching"""
        if dataset_name in self.cached_datasets:
            return self.cached_datasets[dataset_name]

        if dataset_name not in self.file_mapping:
            return None

        file_path = self.file_mapping[dataset_name]

        if not os.path.exists(file_path):
            return None

        print(f"Loading {file_path}...")
        start_time = time.time()

        try:
            gdf = gpd.read_file(file_path)
            load_time = time.time() - start_time
            print(f"Loaded {len(gdf)} features in {load_time:.2f}s")

            self.cached_datasets[dataset_name] = gdf
            return gdf
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None

    def clear_cache(self):
        """Clear the dataset cache"""
        self.cached_datasets.clear()

    def get_cache_info(self) -> Dict[str, int]:
        """Get information about cached datasets"""
        return {name: len(gdf) for name, gdf in self.cached_datasets.items()}


# Global instance for backwards compatibility
data_loader = DataLoader()