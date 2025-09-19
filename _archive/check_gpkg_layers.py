#!/usr/bin/env python3
"""
Check all layers in the GeoPackage to see if we missed anything
"""

import geopandas as gpd
import fiona

def check_gpkg_layers():
    """Check what layers exist in the GeoPackage"""

    gpkg_file = 'oproad_gb.gpkg'

    print("Layers in oproad_gb.gpkg:")
    layers = fiona.listlayers(gpkg_file)

    for layer in layers:
        print(f"\n=== {layer} ===")
        try:
            gdf = gpd.read_file(gpkg_file, layer=layer)
            print(f"Records: {len(gdf)}")
            print(f"Columns: {list(gdf.columns)}")

            # Sample the data
            if len(gdf) > 0:
                print("Sample records:")
                for i in range(min(3, len(gdf))):
                    row = gdf.iloc[i]
                    print(f"  {i+1}: {dict(row.drop('geometry'))}")

                # Check for M25 or bridge-related entries
                if 'road_classification_number' in gdf.columns:
                    m25_entries = gdf[gdf['road_classification_number'].str.contains('M25', na=False)]
                    if len(m25_entries) > 0:
                        print(f"M25 entries in this layer: {len(m25_entries)}")

                if 'name_1' in gdf.columns:
                    bridge_entries = gdf[gdf['name_1'].str.contains('Dartford|Bridge|Tunnel|Crossing', case=False, na=False)]
                    if len(bridge_entries) > 0:
                        print(f"Bridge/tunnel entries: {len(bridge_entries)}")
                        for _, entry in bridge_entries.head(3).iterrows():
                            print(f"  - {entry.get('name_1', 'N/A')} ({entry.get('road_classification_number', 'N/A')})")

        except Exception as e:
            print(f"Error reading layer: {e}")

if __name__ == "__main__":
    check_gpkg_layers()