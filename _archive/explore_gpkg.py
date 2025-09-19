#!/usr/bin/env python3
"""
GeoPackage exploration tool for UK road data
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

def explore_geopackage(gpkg_path):
    """Explore GeoPackage layers and content"""
    print(f"Analyzing GeoPackage: {gpkg_path}")

    # List all layers
    try:
        layers = gpd.list_layers(gpkg_path)
        print(f"\nFound {len(layers)} layer(s):")
        for idx, layer_info in layers.iterrows():
            layer_name = layer_info.get('name', layer_info.get('layer_name', f'layer_{idx}'))
            geom_type = layer_info.get('geom_type', layer_info.get('geometry_type', 'Unknown'))
            fid_count = layer_info.get('fid_count', layer_info.get('feature_count', 'Unknown'))
            print(f"  {layer_name}: {geom_type} ({fid_count} features)")
    except Exception as e:
        print(f"Error listing layers: {e}")
        # Try alternative approach
        try:
            import fiona
            layers_alt = fiona.listlayers(gpkg_path)
            print(f"Found {len(layers_alt)} layer(s): {layers_alt}")
            layers = pd.DataFrame({'name': layers_alt})
        except:
            print("Could not list layers with alternative method")
            return None

    # Analyze each layer
    for idx, layer_info in layers.iterrows():
        layer_name = layer_info['name']
        print(f"\n=== LAYER: {layer_name} ===")

        try:
            gdf = gpd.read_file(gpkg_path, layer=layer_name)

            print(f"Features: {len(gdf)}")
            print(f"CRS: {gdf.crs}")
            print(f"Geometry types: {gdf.geometry.geom_type.value_counts().to_dict()}")
            print(f"Bounds: {gdf.total_bounds}")

            # Analyze columns
            print(f"\nColumns ({len(gdf.columns)} total):")
            for col in gdf.columns:
                if col != 'geometry':
                    col_type = gdf[col].dtype
                    null_count = gdf[col].isnull().sum()
                    print(f"  {col}: {col_type} ({null_count} nulls)")

                    if col_type == 'object':
                        unique_vals = gdf[col].dropna().unique()
                        if len(unique_vals) <= 10:
                            print(f"    Values: {list(unique_vals)}")
                        else:
                            print(f"    {len(unique_vals)} unique values")
                            # Show most common values
                            top_vals = gdf[col].value_counts().head(5)
                            print(f"    Top values: {dict(top_vals)}")

            # Look for road classification columns
            road_cols = [col for col in gdf.columns if any(keyword in col.lower()
                        for keyword in ['road', 'highway', 'class', 'type', 'category'])]

            if road_cols:
                print(f"\nRoad-related columns: {road_cols}")
                for col in road_cols[:3]:  # Analyze first 3
                    if gdf[col].dtype == 'object':
                        print(f"\n{col} distribution:")
                        print(gdf[col].value_counts().head(10))

        except Exception as e:
            print(f"Error reading layer {layer_name}: {e}")

    return layers

def visualize_geopackage(gpkg_path, layers):
    """Create visualization of GeoPackage data"""
    if layers is None or len(layers) == 0:
        print("No layers to visualize")
        return

    # Create subplots based on number of layers
    n_layers = len(layers)
    cols = min(2, n_layers)
    rows = (n_layers + 1) // 2

    fig, axes = plt.subplots(rows, cols, figsize=(15, 8 * rows))
    if n_layers == 1:
        axes = [axes]
    elif rows == 1:
        axes = axes if n_layers > 1 else [axes]
    else:
        axes = axes.flatten()

    for idx, layer_info in layers.iterrows():
        layer_name = layer_info['name']
        ax = axes[idx] if n_layers > 1 else axes[0]

        try:
            gdf = gpd.read_file(gpkg_path, layer=layer_name)

            # Try to color by road type if available
            road_cols = [col for col in gdf.columns if any(keyword in col.lower()
                        for keyword in ['road', 'highway', 'class', 'type', 'category'])]

            if road_cols and gdf[road_cols[0]].dtype == 'object':
                unique_vals = gdf[road_cols[0]].nunique()
                if unique_vals <= 15:  # Only color if manageable number of categories
                    gdf.plot(ax=ax, column=road_cols[0], legend=True,
                           linewidth=0.5, alpha=0.8, cmap='tab10')
                    ax.set_title(f"{layer_name} - Colored by {road_cols[0]}")
                else:
                    gdf.plot(ax=ax, linewidth=0.5, alpha=0.7)
                    ax.set_title(f"{layer_name} ({len(gdf)} features)")
            else:
                gdf.plot(ax=ax, linewidth=0.5, alpha=0.7)
                ax.set_title(f"{layer_name} ({len(gdf)} features)")

            ax.set_axis_off()

        except Exception as e:
            ax.text(0.5, 0.5, f"Error loading\n{layer_name}\n{str(e)}",
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f"{layer_name} (Error)")

    # Hide unused subplots
    for i in range(len(layers), len(axes)):
        axes[i].set_visible(False)

    plt.tight_layout()
    plt.savefig('geopackage_overview.png', dpi=150, bbox_inches='tight')
    plt.show()

def main():
    gpkg_file = "oproad_gb.gpkg"

    if not Path(gpkg_file).exists():
        print(f"GeoPackage file not found: {gpkg_file}")
        return

    print("UK Road GeoPackage Explorer")
    print("===========================")

    layers = explore_geopackage(gpkg_file)

    if layers is not None:
        print("\nCreating visualizations...")
        visualize_geopackage(gpkg_file, layers)
        print("Visualization saved as 'geopackage_overview.png'")

if __name__ == "__main__":
    main()