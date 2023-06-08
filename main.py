
# https://github.com/stephenyeargin/stl-files

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import re
import numpy as np
import sys

class Point:
    def __init__(self,x,y,z):
        self.x = x
        self.y = y
        self.z = z
    
    def __eq__(self, value: object) -> bool:
        return self.x == value.x and self.y == value.y and self.z == value.z
    
    def __str__(self):
        return 'x: {} y: {} z: {}'.format(self.x, self.y, self.z)

class Segment:
    def __init__(self, p: Point, q: Point):
        self.p = p
        self.q = q
    
    def __eq__(self, value: object) -> bool:
        return (self.p == value.p and self.q == value.q) or (self.p == value.q and self.q == value.p)
    
    def __str__(self):
        return 'p: {} q: {}\n'.format(self.p, self.q)
    
    def get_displacement(self)->Point:
        dx = global_round(self.q.x - self.p.x)
        dy = global_round(self.q.y - self.p.y)
        dz = global_round(self.q.z - self.p.z)
        return Point(dx, dy, dz)

class Polygon:
    def __init__(self, points: list[Point]):
        self.points = points
    
    def get_edges(self) -> list[Segment]:
        edges = []
        for i in range(0, len(self.points)-1):
            edges.append(Segment(self.points[i], self.points[i+1]))
        edges.append(Segment(self.points[-1], self.points[0]))
        return edges

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
                    x = global_round(float(d["x"]))
                    y = global_round(float(d["y"]))
                    z = global_round(float(d["z"]))
                    normal = Point(x,y,z)
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
                    x = global_round(float(d["x"]))
                    y = global_round(float(d["y"]))
                    z = global_round(float(d["z"]))
                    points.append(Point(x,y,z))
                if "endloop" in row:
                    if len(points) == 3:
                        polys.append(Polygon(points))
                    points = []
                    state = ParserState.WaitingPoint
                continue
    file.close()
    return polys

def flatten(list):
    return [item for sublist in list for item in sublist]

def intersect_segment_plane(edge: Segment, z_level: float) -> list[Point]:
    d = edge.get_displacement()
    # if dz=0 the edge is parallel to the plane
    if d.z == 0: 
        if edge.q.z == z_level:
            return [edge.p, edge.q]
        else:
            return []
    t = (z_level - edge.p.z) / d.z
    if t<0 or t>1: return []
    x = global_round(edge.p.x + t*d.x)
    y = global_round(edge.p.y + t*d.y)
    z = global_round(edge.p.z + t*d.z)
    return [Point(x,y,z)]

def intersect_polygon_plane(poly: Polygon, z_level: float) -> list[Segment]:
    points = flatten(list(map(lambda edge : intersect_segment_plane(edge, z_level), poly.get_edges())))
    no_duplicate_points = remove_duplicates(points)
    points_n = len(no_duplicate_points)
    if(points_n == 2): return [Segment(no_duplicate_points[0], no_duplicate_points[1])]
    if(points_n == 3): return Polygon(no_duplicate_points).get_edges()
    return []

def draw_layer(layer: list[Segment]):
    for segment in layer:
        vpython.sphere(pos=vpython.vector(segment.p.x, segment.p.y, segment.p.z),radius=0.02)
        vpython.sphere(pos=vpython.vector(segment.q.x, segment.q.y, segment.q.z),radius=0.02)
        vpython.curve(vpython.vector(segment.p.x, segment.p.y, segment.p.z), vpython.vector(segment.q.x, segment.q.y, segment.q.z))

def remove_duplicates(list):
    no_duplicates_list = []
    for elem in list:
        if elem not in no_duplicates_list:
            no_duplicates_list.append(elem)
    return no_duplicates_list

# TODO check if the last edge of the polygon has shared point with the first edge. If so, create a polygon, otherwise it's an open polyline
def polygons_from_segments(segments: list[Segment]):
    if len(segments) == 0: return []
    edges = segments
    current_edge = edges.pop(0)
    polygon_edges: list[Segment] = [current_edge]
    polygons: list[Polygon] = []

    while len(edges)>=0:
        # search for edges that have a point in common with the current new edge
        consecutive_edges_from_q = [edge for edge in edges if current_edge.q == edge.p or current_edge.q == edge.q]
        consecutive_edges_from_p = [edge for edge in edges if current_edge.p == edge.p or current_edge.p == edge.q]
        # if the edge has more than 1 segment in common on one of the two ends, throw an exception
        if len(consecutive_edges_from_p) > 1 or len(consecutive_edges_from_q) > 1:
            raise Exception("Invalid mesh")
        if len(consecutive_edges_from_p) == 1 and (len(consecutive_edges_from_q) == 0 or len(consecutive_edges_from_q) == 1):
            found_edge = consecutive_edges_from_p[0]
        elif len(consecutive_edges_from_p) == 0 and len(consecutive_edges_from_q) == 1:
            found_edge = consecutive_edges_from_q[0]
        else:
            found_edge = None
        
        # print("Current edge: {}".format(current_edge))
        if found_edge is not None:
            # print("Found edge: {}".format(found_edge))
            found_edge_idx = edges.index(found_edge)
            # if it's colinear we merge it with the current edge and we update the last edge of the polygon
            if check_parallel(current_edge, found_edge):
                # print("merge add")
                current_edge = merge_consecutive_parallel(current_edge, found_edge)
                polygon_edges[-1] = current_edge
            # otherwise we add it as a normal edge of the current polygon
            else:
                # print("plain add")
                current_edge = found_edge
                polygon_edges.append(found_edge)
            
            edges.pop(found_edge_idx)
            # print("New current edge: {}".format(current_edge))          
            # then we check if the updated current edge is the end of the polygon
            # we need at least 3 edges to complete a polygon
            # print("Check {} against {}".format(current_edge, polygon_edges[0]))
            if len(polygon_edges) > 2 and check_consecutive(polygon_edges[0], current_edge):
                # it can happen that the last edged of the polygon and the first are colinear. In this case
                # merge them and update the first edge, then delete the last edge
                if check_parallel(polygon_edges[0], current_edge):
                    polygon_edges[0] = merge_consecutive_parallel(polygon_edges[0], current_edge)
                    polygon_edges.pop(-1)
                points = remove_duplicates(flatten([[s.p,s.q] for s in polygon_edges]))
                polygons.append(Polygon(points))
                # print("new polygon: length {}".format(len(points)))
                if len(edges) == 0: break
                current_edge = edges.pop(0)
                polygon_edges = [current_edge]
        else:
            # print("No edges found")
            if len(edges) == 0: break
            current_edge = edges.pop(0)
            polygon_edges = [current_edge]

    return polygons

def merge_consecutive_parallel(s1: Segment, s2: Segment) -> Segment:
    if s1.q == s2.p:
        return Segment(s1.p, s2.q)
    elif s1.q == s2.q:
        return Segment(s1.p, s2.p)
    elif s1.p == s2.q:
        return Segment(s2.p, s1.q)
    else:
        return Segment(s2.q, s1.q)

def check_consecutive(s1: Segment, s2: Segment) -> bool:
    return s1.q == s2.p or s1.p == s2.q or s1.q == s2.q or s1.p == s2.p

def check_parallel(s1: Segment, s2: Segment) -> bool:
    dis1 = s1.get_displacement()
    dis2 = s2.get_displacement()
    if(dis2.x != 0):
        ratio = dis1.x / dis2.x
    elif(dis2.y != 0):
        ratio = dis1.y / dis2.y
    elif(dis2.z != 0):
        ratio = dis1.z / dis2.z
    else:
         return True
    return global_round(dis2.x * ratio) == dis1.x and global_round(dis2.y * ratio) == dis1.y and global_round(dis2.z * ratio) == dis1.z

def global_round(val: float) -> float:
    return round(val, 6)

def main():
    if len(sys.argv)<2:
        print("STL file is missing")
        return
    filename = sys.argv[1]
    # model = parse_stl(filename)
    # layers = dict()
    # model_edges = flatten([poly.get_edges() for poly in model])
    # model_z_values = flatten([[edge.p.z, edge.q.z] for edge in model_edges])
    # model_x_values = flatten([[edge.p.x, edge.q.x] for edge in model_edges])
    # model_y_values = flatten([[edge.p.y, edge.q.y] for edge in model_edges])
    # min_z = min(model_z_values)
    # max_z = max(model_z_values)
    # min_x = min(model_x_values)
    # max_x = max(model_x_values)
    # min_y = min(model_y_values)
    # max_y = max(model_y_values)
    # max_lim = max(max_x, max_y, max_z)
    # min_lim = min(min_x, min_y, min_z)

    # we need to create a layer every 0.1 mm (finest printing), so the step is 0.0001
    # non_optimized_layers = 0
    # optimized_layers = 0
    # step = 0.1
    # for z in np.arange(min_z, max_z, step):
    #     z = round(z, 5)
    #     key = str(z)
    #     layers[key] = []
    #     for poly in model:
    #         segments = intersect_polygon_plane(poly, z)
    #         layers[key] += segments
    #     layers[key] = remove_duplicates(layers[key])
    #     non_optimized_layers+=len(layers[key])
        # print("Original Layer [{}] has {} edges".format(key, len(layers[key])))
        # layers[key] = optimize_segments(layers[key])

        # print("Optimized Layer [{}] has {} edges".format(key, len(layers[key])))
    #     optimized_layers+=len(layers[key])
    
    # print("Non optimized model contains {} segments".format(non_optimized_layers))
    # print("Optimized model layers {} segments".format(optimized_layers))
        
    # def update_chart(val):
    #     keys = [key for key in layers.keys() if float(key)<=val]
    #     for k in keys:
    #         draw_layer(layers[k])

    # scene = vpython.canvas(width=1500, height=1500)
    # update_chart(max_lim)
    # while True:
    #     pass
main()