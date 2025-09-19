#!/usr/bin/env python3
"""
Simplify motorway network by merging consecutive segments with low angle changes
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point
from shapely.ops import linemerge
import numpy as np
from collections import defaultdict, deque
import math

def calculate_bearing(point1, point2):
    """Calculate bearing between two points in degrees"""
    lat1, lon1 = math.radians(point1[1]), math.radians(point1[0])
    lat2, lon2 = math.radians(point2[1]), math.radians(point2[0])

    dlon = lon2 - lon1
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)

    bearing = math.atan2(y, x)
    bearing = math.degrees(bearing)
    return (bearing + 360) % 360

def angle_difference(bearing1, bearing2):
    """Calculate the absolute difference between two bearings"""
    diff = abs(bearing1 - bearing2)
    return min(diff, 360 - diff)

def get_segment_bearing(linestring):
    """Get the overall bearing of a line segment"""
    coords = list(linestring.coords)
    if len(coords) < 2:
        return None

    # Use first and last points for overall direction
    start_point = coords[0]
    end_point = coords[-1]

    return calculate_bearing(start_point, end_point)

def segments_are_connected(seg1, seg2, tolerance=0.0001):
    """Check if two segments are connected (share an endpoint)"""
    seg1_coords = list(seg1.coords)
    seg2_coords = list(seg2.coords)

    seg1_start = Point(seg1_coords[0])
    seg1_end = Point(seg1_coords[-1])
    seg2_start = Point(seg2_coords[0])
    seg2_end = Point(seg2_coords[-1])

    # Check all possible connections
    connections = [
        (seg1_end.distance(seg2_start) < tolerance, 'end_to_start'),
        (seg1_start.distance(seg2_end) < tolerance, 'start_to_end'),
        (seg1_end.distance(seg2_end) < tolerance, 'end_to_end'),
        (seg1_start.distance(seg2_start) < tolerance, 'start_to_start')
    ]

    for connected, connection_type in connections:
        if connected:
            return True, connection_type

    return False, None

def merge_linestrings(line1, line2, connection_type):
    """Merge two linestrings based on their connection type"""
    coords1 = list(line1.coords)
    coords2 = list(line2.coords)

    if connection_type == 'end_to_start':
        # line1 end connects to line2 start
        merged_coords = coords1 + coords2[1:]  # Skip duplicate point
    elif connection_type == 'start_to_end':
        # line1 start connects to line2 end
        merged_coords = coords2 + coords1[1:]  # Skip duplicate point
    elif connection_type == 'end_to_end':
        # line1 end connects to line2 end (reverse line2)
        merged_coords = coords1 + coords2[-2::-1]  # Reverse line2, skip duplicate
    elif connection_type == 'start_to_start':
        # line1 start connects to line2 start (reverse line1)
        merged_coords = coords1[-1::-1] + coords2[1:]  # Reverse line1, skip duplicate
    else:
        raise ValueError(f"Unknown connection type: {connection_type}")

    return LineString(merged_coords)

def simplify_motorway_segments(gdf, angle_threshold=15, max_merge_distance=5000):
    """
    Simplify motorway segments by merging consecutive segments with low angle changes

    Parameters:
    - angle_threshold: Maximum angle difference (degrees) to consider for merging
    - max_merge_distance: Maximum distance (meters) between segments to consider merging
    """

    print(f"Starting simplification with angle threshold: {angle_threshold}°")
    print(f"Original segments: {len(gdf)}")

    # Group by road number
    simplified_segments = []

    road_groups = gdf.groupby('road_classification_number')

    for road_num, road_segments in road_groups:
        print(f"\nProcessing {road_num}: {len(road_segments)} segments")

        if len(road_segments) == 1:
            # Single segment, no simplification needed
            simplified_segments.append(road_segments.iloc[0])
            continue

        # Convert to list for easier processing
        segments_list = list(road_segments.itertuples())
        processed = set()

        for i, segment in enumerate(segments_list):
            if i in processed:
                continue

            # Start a new merged segment
            current_geom = segment.geometry
            current_length = segment.length if hasattr(segment, 'length') else current_geom.length
            current_name = segment.name_1 if hasattr(segment, 'name_1') else None
            merged_indices = {i}

            # Try to merge with following segments
            j = i + 1
            while j < len(segments_list):
                if j in processed:
                    j += 1
                    continue

                next_segment = segments_list[j]
                next_geom = next_segment.geometry

                # Check if segments are connected
                connected, connection_type = segments_are_connected(current_geom, next_geom)

                if connected:
                    # Calculate bearings
                    bearing1 = get_segment_bearing(current_geom)
                    bearing2 = get_segment_bearing(next_geom)

                    if bearing1 is not None and bearing2 is not None:
                        angle_diff = angle_difference(bearing1, bearing2)

                        if angle_diff <= angle_threshold:
                            # Merge the segments
                            try:
                                merged_geom = merge_linestrings(current_geom, next_geom, connection_type)
                                current_geom = merged_geom
                                current_length += next_segment.length if hasattr(next_segment, 'length') else next_geom.length
                                merged_indices.add(j)

                                print(f"  Merged segments {i} and {j} (angle diff: {angle_diff:.1f}°)")

                            except Exception as e:
                                print(f"  Failed to merge segments {i} and {j}: {e}")
                                break
                        else:
                            print(f"  Angle too large ({angle_diff:.1f}°) between segments {i} and {j}")
                            break
                    else:
                        break
                else:
                    # Try next segment
                    pass

                j += 1

            # Add the merged segment
            simplified_segment = segment._asdict()
            simplified_segment['geometry'] = current_geom
            simplified_segment['length'] = current_length
            simplified_segment['merged_from'] = len(merged_indices)

            simplified_segments.append(pd.Series(simplified_segment))
            processed.update(merged_indices)

    # Create new GeoDataFrame
    simplified_gdf = gpd.GeoDataFrame(simplified_segments)
    simplified_gdf.crs = gdf.crs

    print(f"\nSimplification complete:")
    print(f"  Original segments: {len(gdf)}")
    print(f"  Simplified segments: {len(simplified_gdf)}")
    print(f"  Reduction: {((len(gdf) - len(simplified_gdf)) / len(gdf) * 100):.1f}%")

    return simplified_gdf

def main():
    """Main simplification process"""

    print("Loading motorways...")
    motorways = gpd.read_file('motorways_wgs84.geojson')

    print(f"Loaded {len(motorways)} motorway segments")
    print(f"Coordinate system: {motorways.crs}")

    # Simplify the segments
    simplified = simplify_motorway_segments(
        motorways,
        angle_threshold=20,  # 20 degree threshold
        max_merge_distance=5000  # 5km max distance
    )

    # Save simplified version
    output_file = 'simplified_motorways_wgs84.geojson'
    simplified.to_file(output_file, driver='GeoJSON')
    print(f"\nSimplified motorways saved to: {output_file}")

    # Show statistics by road
    print(f"\nSimplification by road:")
    original_counts = motorways['road_classification_number'].value_counts()
    simplified_counts = simplified['road_classification_number'].value_counts()

    for road in sorted(original_counts.index):
        orig = original_counts.get(road, 0)
        simp = simplified_counts.get(road, 0)
        reduction = ((orig - simp) / orig * 100) if orig > 0 else 0
        print(f"  {road}: {orig} → {simp} segments ({reduction:.1f}% reduction)")

if __name__ == "__main__":
    main()