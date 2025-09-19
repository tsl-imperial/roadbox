#!/usr/bin/env python3
"""
GeoJSON-compatible compression using Douglas-Peucker simplification and coordinate precision reduction
"""

import geopandas as gpd
import json
import os
from shapely.geometry import LineString, MultiLineString

def reduce_coordinate_precision(coords, precision=4):
    """Reduce coordinate precision to specified decimal places"""
    if not coords:
        return coords

    return [[round(coord[0], precision), round(coord[1], precision)] for coord in coords]

def simplify_geometry(geometry, tolerance=0.001, precision=4):
    """Simplify geometry using Douglas-Peucker and reduce coordinate precision"""

    # Apply Douglas-Peucker simplification
    simplified_geom = geometry.simplify(tolerance=tolerance, preserve_topology=True)

    # Extract coordinates and reduce precision
    if simplified_geom.geom_type == 'LineString':
        coords = list(simplified_geom.coords)
        reduced_coords = reduce_coordinate_precision(coords, precision)
        return LineString(reduced_coords)

    elif simplified_geom.geom_type == 'MultiLineString':
        simplified_lines = []
        for line in simplified_geom.geoms:
            coords = list(line.coords)
            reduced_coords = reduce_coordinate_precision(coords, precision)
            if len(reduced_coords) >= 2:  # Valid LineString needs at least 2 points
                simplified_lines.append(LineString(reduced_coords))

        if simplified_lines:
            return MultiLineString(simplified_lines)
        else:
            # Fallback to original if simplification removed too much
            return geometry

    return simplified_geom

def compress_motorways(input_file, output_file, tolerance=0.001, precision=4):
    """
    Compress motorway GeoJSON using Douglas-Peucker simplification and coordinate precision reduction

    Parameters:
    - tolerance: Douglas-Peucker tolerance in degrees (~0.001 = ~100m)
    - precision: Decimal places for coordinates (4 = ~10m precision)
    """

    print(f"Loading {input_file}...")
    gdf = gpd.read_file(input_file)

    original_size = os.path.getsize(input_file)
    print(f"Original file size: {original_size / (1024*1024):.2f} MB")
    print(f"Original segments: {len(gdf)}")

    # Calculate original coordinate count
    original_coords = 0
    for geom in gdf.geometry:
        if geom.geom_type == 'LineString':
            original_coords += len(geom.coords)
        elif geom.geom_type == 'MultiLineString':
            for line in geom.geoms:
                original_coords += len(line.coords)

    print(f"Original coordinate points: {original_coords:,}")

    # Apply compression
    print(f"\nApplying compression:")
    print(f"  Douglas-Peucker tolerance: {tolerance} degrees (~{tolerance * 111000:.0f}m)")
    print(f"  Coordinate precision: {precision} decimal places (~{10**(1-precision)*111000:.0f}m accuracy)")

    compressed_geometries = []
    simplified_coords = 0

    for i, geom in enumerate(gdf.geometry):
        if i % 1000 == 0:
            print(f"  Processing segment {i}/{len(gdf)}")

        simplified_geom = simplify_geometry(geom, tolerance, precision)
        compressed_geometries.append(simplified_geom)

        # Count simplified coordinates
        if simplified_geom.geom_type == 'LineString':
            simplified_coords += len(simplified_geom.coords)
        elif simplified_geom.geom_type == 'MultiLineString':
            for line in simplified_geom.geoms:
                simplified_coords += len(line.coords)

    # Update geometries
    gdf_compressed = gdf.copy()
    gdf_compressed.geometry = compressed_geometries

    # Save compressed version
    print(f"\nSaving compressed file...")
    gdf_compressed.to_file(output_file, driver='GeoJSON')

    # Calculate compression statistics
    compressed_size = os.path.getsize(output_file)
    size_reduction = (1 - compressed_size / original_size) * 100
    coord_reduction = (1 - simplified_coords / original_coords) * 100

    print(f"\nCompression Results:")
    print(f"  Original size: {original_size / (1024*1024):.2f} MB")
    print(f"  Compressed size: {compressed_size / (1024*1024):.2f} MB")
    print(f"  Size reduction: {size_reduction:.1f}%")
    print(f"  ")
    print(f"  Original coordinates: {original_coords:,}")
    print(f"  Compressed coordinates: {simplified_coords:,}")
    print(f"  Coordinate reduction: {coord_reduction:.1f}%")
    print(f"  ")
    print(f"  Segments: {len(gdf)} (unchanged)")

def compare_tolerances():
    """Test different tolerance levels to find optimal compression"""

    print("Testing different compression levels...")

    # Test with small sample first
    gdf = gpd.read_file('motorways_wgs84.geojson')
    sample = gdf.head(100)  # Test with first 100 segments

    tolerances = [0.0001, 0.0005, 0.001, 0.002, 0.005]  # ~10m to 500m

    for tolerance in tolerances:
        print(f"\nTesting tolerance: {tolerance} degrees (~{tolerance * 111000:.0f}m)")

        original_coords = 0
        simplified_coords = 0

        for geom in sample.geometry:
            # Count original
            if geom.geom_type == 'LineString':
                original_coords += len(geom.coords)
            elif geom.geom_type == 'MultiLineString':
                for line in geom.geoms:
                    original_coords += len(line.coords)

            # Count simplified
            simplified_geom = simplify_geometry(geom, tolerance, precision=4)
            if simplified_geom.geom_type == 'LineString':
                simplified_coords += len(simplified_geom.coords)
            elif simplified_geom.geom_type == 'MultiLineString':
                for line in simplified_geom.geoms:
                    simplified_coords += len(line.coords)

        reduction = (1 - simplified_coords / original_coords) * 100
        print(f"  Coordinate reduction: {reduction:.1f}%")

def main():
    """Main compression process"""

    input_file = 'motorways_wgs84.geojson'

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        return

    # Test different compression levels first
    print("=== COMPRESSION LEVEL TESTING ===")
    compare_tolerances()

    print("\n" + "="*50)
    print("=== FULL COMPRESSION ===")

    # Apply optimal compression
    output_file = 'motorways_compressed.geojson'
    compress_motorways(
        input_file=input_file,
        output_file=output_file,
        tolerance=0.001,  # ~100m tolerance - good balance
        precision=4       # ~10m coordinate precision
    )

    print(f"\nCompressed motorways saved to: {output_file}")

if __name__ == "__main__":
    main()