
# https://github.com/stephenyeargin/stl-files

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import re
import numpy as np

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

def parse_stl(filename: str) -> list[Polygon]:
    regex_point = re.compile(r"(.+)?vertex (?P<x>-?\d+\.\d+) (?P<y>-?\d+\.\d+) (?P<z>-?\d+\.\d+)")
    polys = []
    with open(filename, mode='r') as file:
        state = ParserState.WaitingPoint
        points = []
        for row in file:
            if state == ParserState.WaitingPoint:
                if "outer loop" in row:
                    state = ParserState.ReadingPoint
                continue
            if state == ParserState.ReadingPoint:
                if "vertex" in row:
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

def draw_layer(layer: list[Segment], ax):
    for segment in layer:
        # ax.scatter(segment.p.x, segment.p.y, segment.p.z)
        # ax.scatter(segment.q.x, segment.q.y, segment.q.z)
        ax.plot([segment.p.x, segment.q.x], [segment.p.y, segment.q.y], [segment.p.z, segment.q.z], color='blue')

def remove_duplicates(list):
    no_duplicates_list = []
    for elem in list:
        if elem not in no_duplicates_list:
            no_duplicates_list.append(elem)
    return no_duplicates_list

def optimize_segments(segments: list[Segment]):
    if len(segments) == 0:
        return []
    new_edges = []
    edges = segments
    new_edge = edges.pop(0)
    while len(edges)>0:
        consecutive_edges_from_p = [edge for edge in edges if new_edge.p == edge.p or new_edge.p == edge.q]
        consecutive_edges_from_q = [edge for edge in edges if new_edge.q == edge.p or new_edge.q == edge.q]

        consecutive_edges = []
        # if there more than 1 consecutive edge from the same point of the segment we don't optimize
        if len(consecutive_edges_from_p) == 1:
            consecutive_edges.append(consecutive_edges_from_p[0])
        if len(consecutive_edges_from_q) == 1:
            consecutive_edges.append(consecutive_edges_from_q[0])
        
        merged = False
        for e in consecutive_edges:
            if len(edges) == 0: break
            # we search inside the edges to retrieve the correct index but we also need to check if the edges are consecutive
            c_parallel_edges = [i for i, edge in enumerate(edges) if check_parallel(new_edge, edge) and edge == e]
            if len(c_parallel_edges) == 1:
                idx = c_parallel_edges[0]
                found_edge = edges[idx]
                new_edge = merge_consecutive_parallel(new_edge, found_edge)
                edges.pop(idx)
                merged = True
        
        if not merged:
            new_edges.append(new_edge)
            new_edge = edges.pop(0)
    
    new_edges.append(new_edge)
    return new_edges

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
    model = parse_stl("examples/example5.stl")
    layers = dict()
    fig = plt.figure()
    # plt.autoscale(False)
    ax = fig.add_subplot(projection='3d')      
    model_edges = flatten([poly.get_edges() for poly in model])
    model_z_values = flatten([[edge.p.z, edge.q.z] for edge in model_edges])
    model_x_values = flatten([[edge.p.x, edge.q.x] for edge in model_edges])
    model_y_values = flatten([[edge.p.y, edge.q.y] for edge in model_edges])
    min_z = min(model_z_values)
    max_z = max(model_z_values)
    min_x = min(model_x_values)
    max_x = max(model_x_values)
    min_y = min(model_y_values)
    max_y = max(model_y_values)
    max_lim = max(max_x, max_y, max_z)
    min_lim = min(min_x, min_y, min_z)

    # we need to create a layer every 0.1 mm (finest printing), so the step is 0.0001
    non_optimized_layers = 0
    optimized_layers = 0
    step = 0.1
    for z in np.arange(min_z, max_z, step):
        z = round(z, 5)
        key = str(z)
        layers[key] = []
        for poly in model:
            segments = intersect_polygon_plane(poly, z)
            layers[key] += segments
        layers[key] = remove_duplicates(layers[key])
        non_optimized_layers+=len(layers[key])
        print("Original Layer [{}] has {} edges".format(key, len(layers[key])))
        layers[key] = optimize_segments(layers[key])
        print("Optimized Layer [{}] has {} edges".format(key, len(layers[key])))
        optimized_layers+=len(layers[key])
    
    print("Non optimized model contains {} segments".format(non_optimized_layers))
    print("Optimized model layers {} segments".format(optimized_layers))
        
    axfreq = fig.add_axes([0.1,0.85,0.8,0.1])
    z_slider = Slider(
        ax=axfreq,
        label='Layer (z)',
        valmin=min_z,
        valmax=max_z,
        valinit=min_z,
        valstep=step
    )

    def update_chart(val):
        ax.cla()
        ax.set_xlim(min_lim, max_lim)
        ax.set_ylim(min_lim, max_lim)
        ax.set_zlim(min_lim, max_lim)
        keys = [key for key in layers.keys() if float(key)<=val]
        for k in keys:
            draw_layer(layers[k], ax)
    
    update_chart(min_lim)

    z_slider.on_changed(update_chart)
    plt.show()
main()