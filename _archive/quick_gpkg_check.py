#!/usr/bin/env python3
"""
Quick GeoPackage layer check
"""

import fiona
import geopandas as gpd

def quick_check(gpkg_path):
    print(f"Quick check of {gpkg_path}")

    # List layers
    try:
        layers = fiona.listlayers(gpkg_path)
        print(f"Layers: {layers}")

        # Check first layer quickly
        if layers:
            first_layer = layers[0]
            print(f"\nChecking layer: {first_layer}")

            # Read just a few features
            gdf = gpd.read_file(gpkg_path, layer=first_layer, rows=5)
            print(f"Sample features: {len(gdf)}")
            print(f"Columns: {list(gdf.columns)}")
            print(f"CRS: {gdf.crs}")

            # Show sample data
            print("\nSample data:")
            for col in gdf.columns:
                if col != 'geometry':
                    print(f"  {col}: {gdf[col].iloc[0] if len(gdf) > 0 else 'No data'}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    quick_check("oproad_gb.gpkg")