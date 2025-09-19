#!/usr/bin/env python3
"""
Comprehensive analysis of oproad_gb.gpkg
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import fiona

def analyze_all_layers():
    """Analyze all layers in the GeoPackage"""
    gpkg_path = "oproad_gb.gpkg"
    layers = fiona.listlayers(gpkg_path)

    print("UK Open Roads GeoPackage Analysis")
    print("================================")
    print(f"Layers found: {layers}\n")

    layer_data = {}

    for layer in layers:
        print(f"=== LAYER: {layer} ===")

        # Read full layer
        gdf = gpd.read_file(gpkg_path, layer=layer)
        layer_data[layer] = gdf

        print(f"Total features: {len(gdf):,}")
        print(f"CRS: {gdf.crs}")
        print(f"Geometry types: {gdf.geometry.geom_type.value_counts().to_dict()}")

        # Column analysis
        print(f"Columns ({len(gdf.columns)}):")
        for col in gdf.columns:
            if col != 'geometry':
                dtype = gdf[col].dtype
                nulls = gdf[col].isnull().sum()
                print(f"  {col}: {dtype} ({nulls:,} nulls)")

                if dtype == 'object' and nulls < len(gdf):
                    unique_count = gdf[col].nunique()
                    if unique_count <= 20:
                        print(f"    Unique values ({unique_count}): {sorted(gdf[col].dropna().unique())}")
                    else:
                        print(f"    {unique_count:,} unique values")
                        top_values = gdf[col].value_counts().head(5)
                        print(f"    Top values: {dict(top_values)}")
        print()

    return layer_data

def create_visualizations(layer_data):
    """Create visualizations for each layer"""
    n_layers = len(layer_data)
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    axes = axes.flatten()

    # Plot each layer
    for i, (layer_name, gdf) in enumerate(layer_data.items()):
        ax = axes[i]

        if layer_name == 'road_link':
            # For roads, try to color by road classification
            road_cols = [col for col in gdf.columns if 'class' in col.lower() or 'type' in col.lower()]
            if road_cols:
                col_to_use = road_cols[0]
                unique_vals = gdf[col_to_use].nunique()
                if unique_vals <= 15:
                    gdf.plot(ax=ax, column=col_to_use, legend=True,
                           linewidth=0.3, alpha=0.8, cmap='tab10')
                    ax.set_title(f"{layer_name} - Colored by {col_to_use}")
                else:
                    gdf.plot(ax=ax, linewidth=0.3, alpha=0.7)
                    ax.set_title(f"{layer_name} ({len(gdf):,} features)")
            else:
                gdf.plot(ax=ax, linewidth=0.3, alpha=0.7)
                ax.set_title(f"{layer_name} ({len(gdf):,} features)")
        else:
            # For points (junctions, nodes)
            gdf.plot(ax=ax, markersize=1, alpha=0.7)
            ax.set_title(f"{layer_name} ({len(gdf):,} features)")

        ax.set_axis_off()

    # Overall combined view
    if len(layer_data) < 4:
        ax = axes[3]
        for layer_name, gdf in layer_data.items():
            if 'link' in layer_name:
                gdf.plot(ax=ax, linewidth=0.2, alpha=0.6, label=layer_name)
            else:
                gdf.plot(ax=ax, markersize=0.5, alpha=0.8, label=layer_name)
        ax.set_title("All Layers Combined")
        ax.legend()
        ax.set_axis_off()

    plt.tight_layout()
    plt.savefig('oproad_analysis.png', dpi=150, bbox_inches='tight')
    plt.show()

def road_classification_analysis(layer_data):
    """Detailed analysis of road classifications"""
    if 'road_link' not in layer_data:
        print("No road_link layer found for classification analysis")
        return

    road_gdf = layer_data['road_link']
    print("Road Classification Analysis")
    print("===========================")

    # Find classification columns
    class_cols = [col for col in road_gdf.columns if any(keyword in col.lower()
                 for keyword in ['class', 'type', 'category', 'function'])]

    for col in class_cols:
        print(f"\n{col} distribution:")
        counts = road_gdf[col].value_counts()
        print(counts.head(15))

        # Calculate total length by classification if length column exists
        length_cols = [c for c in road_gdf.columns if 'length' in c.lower()]
        if length_cols:
            length_col = length_cols[0]
            length_by_class = road_gdf.groupby(col)[length_col].sum().sort_values(ascending=False)
            print(f"\nTotal length by {col}:")
            for class_name, total_length in length_by_class.head(10).items():
                print(f"  {class_name}: {total_length:,.0f}")

def main():
    layer_data = analyze_all_layers()

    print("Creating visualizations...")
    create_visualizations(layer_data)

    road_classification_analysis(layer_data)

    print(f"\nAnalysis complete!")
    print(f"Visualization saved as 'oproad_analysis.png'")

if __name__ == "__main__":
    main()