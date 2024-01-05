
# https://github.com/stephenyeargin/stl-files

# import vpython
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import re
import numpy as np
import sys
from math import atan2, pi, atan2

class Segment:
    def __init__(self, p, q, normal = np.array([1, 0, 0])):
        self.p = p
        self.q = q
        self.normal = normal
    
    def __eq__(self, value: object) -> bool:
        return (np.array_equal(self.p, value.p) and np.array_equal(self.q, value.q)) or (np.array_equal(self.p, value.q) and np.array_equal(self.q, value.p))

    def __ne__(self, value: object) -> bool:
        return not self.__eq__(value)
    
    def __str__(self):
        return 'p: {} q: {} normal: {}\n'.format(self.p, self.q, self.normal)
    
    def get_displacement(self):
        return self.q - self.p

class Polygon:
    def __init__(self, points, normal = np.array([1, 0, 0])):
        self.points = points
        self.normal = normal
    
    def get_edges(self) -> list[Segment]:
        edges = []
        for i in range(0, len(self.points)-1):
            edges.append(Segment(self.points[i], self.points[i+1], self.normal))
        edges.append(Segment(self.points[-1], self.points[0], self.normal))
        return edges

    def get_centroid(self):
        return compute_centroid(self.points)

def compute_centroid(points):
    p = []
    for i in range(len(points[0])):
        c = sum(p[i] for p in points) / len(points)
        p.append(c)
    return np.array(p)

def compute_magnitude(vec):
    return np.sqrt(sum([c**2 for c in vec]))

def compute_angle(vec):
    return atan2(vec[1], vec[0])

def compute_angle_from_center(point, center):
    delta = point - center
    return compute_angle(delta)

def compute_angle_between(vec1, vec2):
    n = np.dot(vec1, vec2)
    d = compute_magnitude(vec1) * compute_magnitude(vec2)
    return np.arccos(n/d)

def mod2pi(angle: float) -> float:
    angle = angle % (2*pi)
    if angle < 0:
        angle += (2*pi)
    return angle

def check_parallel(vec1, vec2) -> bool:
    return np.cross(vec1, vec2) == 0

def order_points_clockwise(points):
    if len(points) == 0:
        return []
    centroid = compute_centroid(points)
    return sorted(points, key=lambda p: compute_angle_from_center(p, centroid))

class ParserState:
    WaitingPoint = 0
    ReadingPoint = 1
    WaitingNormal = 2

def parse_stl(filename: str) -> list[Polygon]:
    regex_point = re.compile(r"(.+)?vertex (?P<x>-?\d+\.\d+) (?P<y>-?\d+\.\d+) (?P<z>-?\d+\.\d+)")
    regex_normal = re.compile(r"(.+)?facet normal (?P<x>-?\d+\.\d+) (?P<y>-?\d+\.\d+) (?P<z>-?\d+\.\d+)")
    polys = []
    with open(filename, mode='r') as file:
        state = ParserState.WaitingNormal
        points = []
        normal = None
        for row in file:
            if state == ParserState.WaitingNormal:
                r = regex_normal.match(row)
                if r:
                    d = r.groupdict()
                    x = float(d["x"])
                    y = float(d["y"])
                    z = float(d["z"])
                    normal = np.array([x,y,z])
                    state = ParserState.WaitingPoint
                continue
            if state == ParserState.WaitingPoint:
                if "outer loop" in row:
                    state = ParserState.ReadingPoint
                continue
            if state == ParserState.ReadingPoint:
                r = regex_point.match(row)
                if r:
                    d = r.groupdict()
                    x = float(d["x"])
                    y = float(d["y"])
                    z = float(d["z"])
                    points.append(np.array([x, y, z]))
                if "endloop" in row:
                    if len(points) == 3:
                        # print(normal)
                        polys.append(Polygon(points, normal))
                    points = []
                    state = ParserState.WaitingNormal
                continue
    file.close()
    return polys

def intersect_segment_plane(edge: Segment, z_level: float):
    d = edge.get_displacement()
    # if dz=0 the edge is parallel to the plane
    if global_round(d[2]) == 0:
        if edge.q[2] == z_level or edge.p[2] == z_level:
            return [edge.p, edge.q]
        else:
            return []
    
    t = (z_level - edge.p[2]) / d[2]
    if t<0 or t>1:
        return []
    
    point = edge.p + (t * d)
    return [point]

# polygons are triangles
# there are several cases:
# 1 - the triangle intersects the z plane with 1 edge: in this case, the intersections will be 1 edge and 2 points, 
# which are the ends of the edge that are the intersections between the other two edges and the z plane
# 2 - the triangle fully stays in the plane: in this case, the intersection will be 3 edges and 0 points
# 3 - the triangle is split in 2 halfs by the plane: in this case, the intersections will be 2 points,
# that must become a single edge
# 4 - the triangle intersects the z plane in 1 vertex: in this case, the intersections will be 2 points, one for each segments, that must be merged in 1 single point
# 5 - the triangle doesn't interect the plane at all: in this case, the interection will be 0 points
# 6 - the triangle intersects the z plane in 1 vertex and 1 edge: in this case, the intersections will be 3 point, 2 equals (like case 4, must be merged in 1 single), and another point.
# These 2 must become a single edge

def intersect_polygon_plane(poly: Polygon, z_level: float):
    # get intersections
    intersections = [intersect_segment_plane(edge, z_level) for edge in poly.get_edges()]
    # remove empty intersections
    intersections = [s for s in intersections if len(s) > 0]

    # remove single point duplicates
    single_point_intersections = [s for s in intersections if len(s) == 1]
    single_point_intersections = remove_duplicates(single_point_intersections, lambda a,b: np.array_equal(a[0], b[0]))

    double_point_intersections = [s for s in intersections if len(s) == 2]

    if double_point_intersections == 1:
        intersections = double_point_intersections
    elif len(single_point_intersections) == 2:
        intersections = [flatten(single_point_intersections)]
    else:
        intersections = [*single_point_intersections, *double_point_intersections]
    
    return intersections
    # points = remove_duplicates(points)
    # return order_points_clockwise(points)

# def draw_layer(layer: list[Segment]):
#     for segment in layer:
#         vpython.sphere(pos=vpython.vector(segment.p.x, segment.p.y, segment.p.z),radius=0.02)
#         vpython.sphere(pos=vpython.vector(segment.q.x, segment.q.y, segment.q.z),radius=0.02)
        # vpython.curve(vpython.vector(segment.p.x, segment.p.y, segment.p.z), vpython.vector(segment.q.x, segment.q.y, segment.q.z))

def remove_duplicates(l, pred):
    no_duplicates = []
    for elem in l:
        found = False
        for elem2 in no_duplicates:
            if pred(elem, elem2):
                found = True
        if not found:
            no_duplicates.append(elem)
    
    return no_duplicates

def flatten(list):
    return [item for sublist in list for item in sublist]

# def merge_consecutive_parallel(s1: Segment, s2: Segment) -> Segment:
#     if s1.q == s2.p:
#         return Segment(s1.p, s2.q, s1.normal)
#     elif s1.q == s2.q:
#         return Segment(s1.p, s2.p, s1.normal)
#     elif s1.p == s2.q:
#         return Segment(s2.p, s1.q, s1.normal)
#     else:
#         return Segment(s2.q, s1.q, s1.normal)

def check_consecutive(s1: Segment, s2: Segment) -> bool:
    return s1.q == s2.p or s1.p == s2.q or s1.q == s2.q or s1.p == s2.p

def global_round(val: float) -> float:
    return round(val, 6)

def main():
    if len(sys.argv) < 2:
        print("STL file is missing")
        return
    filename = sys.argv[1]
    model = parse_stl(filename)
    layers = dict()
    model_edges = flatten([poly.get_edges() for poly in model])
    model_z_values = flatten([[edge.p[2], edge.q[2]] for edge in model_edges])
    min_z = min(model_z_values)
    max_z = max(model_z_values)

    # we need to create a layer every 0.1 mm (finest printing), so the step is 0.0001
    # non_optimized_layers = 0
    # optimized_layers = 0
    step = 0.05
    for z in np.arange(min_z, max_z + step, step):
        z = global_round(z)
        key = str(z)
        layers[key] = []
        layer_intersections = []
        print(f'layer: {z}')
        for poly in model:
            segments = intersect_polygon_plane(poly, z)
            if len(segments) > 0:
                # print(f'Segments: {segments}')
                layer_intersections += segments
        # layer_intersections = remove_duplicates(layer_intersections)
        print("Segments found: ",len(layer_intersections))
        # non_optimized_layers+=len(layers[key])
        # print("Original Layer [{}] has {} edges".format(key, len(layers[key])))
        # try:
        #     layers[key] = surfaces_from_segments(layer_segments)
        #     print("Polygons found: ",len(layers[key]))
        #     for surf in layers[key]:
        #         print("len {} infill {}".format(len(surf.points), surf.fill))
        # except Exception as e:
        #     print(e)
        #     continue   
    # print("Non optimized model contains {} segments".format(non_optimized_layers))
    # print("Optimized model layers {} segments".format(optimized_layers))
        
    # def update_chart(val):
    #     keys = [key for key in layers.keys() if float(key)<=val]
    #     for k in keys:
    #         for p in layers[k]:
    #             pass
    #             # draw_layer(p.poly.get_edges())

    # vpython.canvas(width=1500, height=1500)
    # update_chart(max_z)
    # while True:
    #     pass

if __name__ == "__main__":
    main()