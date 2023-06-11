import unittest
from main import intersect_segment_plane, intersect_polygon_plane, check_consecutive, check_parallel, Segment, Point, Polygon, surfaces_from_segments, parse_stl

class TestGeometry(unittest.TestCase):

    def test_intersect_segment_plane_1(self):
        s = Segment(Point(1,0,0), Point(2,0,0),Point(0,0,0))
        points = intersect_segment_plane(s, 0)
        self.assertTrue(len(points) == 2)
    
    def test_intersect_segment_plane_2(self):
        s = Segment(Point(1,0,0), Point(2,0,0))
        points = intersect_segment_plane(s, 1)
        self.assertTrue(len(points) == 0)
    
    def test_intersect_segment_plane_3(self):
        s = Segment(Point(1,0,0), Point(1,0,1))
        points = intersect_segment_plane(s, 0.5)
        self.assertTrue(len(points) == 1)

    def test_intersect_segment_plane_4(self):
        s = Segment(Point(1,0,0), Point(1,0,1))
        points = intersect_segment_plane(s, 1)
        self.assertTrue(len(points) == 1)

    def test_intersect_polygon_plane_1(self):
        p = Polygon([Point(1,0,0), Point(1,1,0), Point(0,1,0)])
        points = intersect_polygon_plane(p, 1)
        self.assertTrue(len(points) == 0)

    # if the polygon belongs entirely to the plane, return segments
    def test_intersect_polygon_plane_2(self):
        p = Polygon([Point(1,0,0), Point(1,1,0), Point(0,1,0)])
        segments = intersect_polygon_plane(p, 0)
        self.assertTrue(len(segments) == 0)

    def test_intersect_polygon_plane_3(self):
        p = Polygon([Point(1,0,0), Point(1,1,0), Point(1,1,1)], Point(1,0,0))
        segments = intersect_polygon_plane(p, 0.5)
        self.assertEqual(len(segments), 1)
    
    def test_intersect_polygon_plane_4(self):
        p = Polygon([Point(1,0,0), Point(1,1,0), Point(0,0,1)])
        segments = intersect_polygon_plane(p, 1)
        self.assertTrue(len(segments) == 0)

    def test_consecutive_1(self):
        s1 = Segment(Point(1,0,0), Point(2,0,0))
        s2 = Segment(Point(2,0,0), Point(3,0,0))
        self.assertTrue(check_consecutive(s1,s2))

    def test_consecutive_2(self):
        s1 = Segment(Point(2,0,0), Point(3,0,0))
        s2 = Segment(Point(1,0,0), Point(2,0,0))
        self.assertTrue(check_consecutive(s1,s2))
    
    def test_consecutive_3(self):
        s1 = Segment(Point(2,0,1), Point(3,0,2))
        s2 = Segment(Point(3,0,2), Point(1,0,1))
        self.assertTrue(check_consecutive(s1,s2))
    
    def test_consecutive_4(self):
        s1 = Segment(Point(1,0,1), Point(3,0,5))
        s2 = Segment(Point(3,0,2), Point(1,0,4))
        self.assertFalse(check_consecutive(s1,s2))

    def test_consecutive_5(self):
        s1 = Segment(Point(-1.846087, -1.846087, -0.01099), Point(-1.846087, -0.18279735946805542, -0.01099))
        s2 = Segment(Point(-1.846087, -0.18279735946805542, -0.01099), Point(-1.846087, 1.846087, -0.01099))
        self.assertTrue(check_consecutive(s1,s2))
    
    def test_consecutive_6(self):
        s1 = Segment(Point(-1.846087, 1.846087, -0.01099), Point(1.507202, 1.846087, -0.01099))
        s2 = Segment(Point(1.846087, 1.846087, -0.01099),Point(1.507202, 1.846087, -0.01099))
        self.assertTrue(check_consecutive(s1,s2))
    
    def test_parallel_1(self):
        s1 = Segment(Point(1,0,0), Point(1,0,1))
        s2 = Segment(Point(2,0,0), Point(2,0,1))
        self.assertTrue(check_parallel(s1,s2))
    
    def test_parallel_2(self):
        s1 = Segment(Point(1,0,0), Point(2,0,0))
        s2 = Segment(Point(1,1,0), Point(2,1,0))
        self.assertTrue(check_parallel(s1,s2))

    def test_parallel_3(self):
        s1 = Segment(Point(1,0,0), Point(2,0,0))
        s2 = Segment(Point(1,0,2), Point(2,0,3))
        self.assertFalse(check_parallel(s1,s2))

    def test_parallel_4(self):
        s1 = Segment(Point(1,0,0), Point(2,0,0))
        s2 = Segment(Point(-1,0,0), Point(-2,0,0))
        self.assertTrue(check_parallel(s1,s2))
    
    def test_parallel_5(self):
        s1 = Segment(Point(-1.846087, -1.846087, -0.01099), Point(-1.846087, -0.182797, -0.01099))
        s2 = Segment(Point(-1.846087, -0.1827973, -0.01099), Point(-1.846087, 1.846087, -0.01099))
        self.assertTrue(check_parallel(s1,s2))
    
    def test_parallel_6(self):
        s1 = Segment(Point(-2, -2, 0), Point(-2, -1, 0))
        s2 = Segment(Point(-2, -1, 0), Point(-2, 2, 0))
        self.assertTrue(check_parallel(s1,s2))

    def test_parallel_7(self):
        s1 = Segment(Point(1.846087, 1.846087, -0.01099), Point(1.846087, -0.377563, -0.01099))
        s2 = Segment(Point(-2, -1, 0), Point(-2, 2, 0))
        self.assertTrue(check_parallel(s1,s2))
    
    def test_parallel_8(self):
        s1 = Segment(Point(-1.846087, 1.846087, -0.01099), Point(1.507202, 1.846087, -0.01099))
        s2 = Segment(Point(1.846087, 1.846087, -0.01099),Point(1.507202, 1.846087, -0.01099))
        self.assertTrue(check_parallel(s1,s2))
    
    def test_optimize_segments_1(self):
        segments = [Segment(Point(0,0,0), Point(1,0,0)), Segment(Point(1,0,0), Point(2,0,0))]
        result = surfaces_from_segments(segments)
        self.assertEqual(len(result),0) 
    
    def test_optimize_segments_2(self):
        segments = [Segment(Point(0,0,0), Point(1,0,0)), Segment(Point(1,0,0), Point(2,0,0)), Segment(Point(-1,0,0), Point(0,0,0))]
        result = surfaces_from_segments(segments)
        self.assertEqual(len(result),0)

    def test_optimize_segments_3(self):
        segments = [Segment(Point(0,0,0), Point(1,0,0), Point(0,1,0)), Segment(Point(1,0,0), Point(1,1,0), Point(1,0,0)), Segment(Point(1,1,0), Point(0,0,0), Point(-0.5,-0.5,0)), Segment(Point(-4,0,0), Point(-2,0,0), Point(0,0,0))]
        result = surfaces_from_segments(segments)
        self.assertEqual(len(result),1)
        self.assertEqual(len(result[0].points),3)
    
    # def test_optimize_segments_4(self):

    #     segments = [
    #         Segment(Point(1,-1,0), Point(2,-3,0)),
    #         Segment(Point(4,1,0), Point(4,2,0)),
    #         Segment(Point(2,1,0), Point(3,1,0)),
    #         Segment(Point(4,1,0), Point(3,1,0)),
    #         Segment(Point(3,3,0), Point(2,4,0)),
    #         Segment(Point(7,0,0), Point(8,0,0)),
    #         Segment(Point(4,2,0), Point(3,3,0)),
    #         Segment(Point(2,4,0), Point(1,3,0)),
    #         Segment(Point(1,3,0), Point(2,1,0)),
    #         Segment(Point(1,-1,0), Point(2,-1,0)),
    #         Segment(Point(2,-1,0), Point(2,-3,0)),
    #         Segment(Point(6,0,0), Point(7,0,0)),
    #     ]
    #     result = surfaces_from_segments(segments)
    #     self.assertEqual(len(result), 2)
    #     self.assertEqual(len(result[1].poly.get_edges()), 5)
    #     self.assertEqual(len(result[0].poly.get_edges()), 3)
    
    # def test_optimize_segments_5(self):
    #     segments = [
    #         Segment(Point(-1.846087, -1.846087,-0.01099), Point(-1.846087, -0.182797,-0.01099)),
    #         Segment(Point(-1.846087, -0.182797,-0.01099), Point(-1.846087, 1.846087,-0.01099)),
    #         Segment(Point( 1.846087, 1.846087,-0.01099), Point(1.846087, -0.182797,-0.01099)),
    #         Segment(Point( 1.846087, -0.182797,-0.01099), Point(1.846087, -0.377563,-0.01099)),
    #         Segment(Point( 1.846087, -1.846087,-0.01099), Point(1.846087, -1.244798,-0.01099)),
    #         Segment(Point( 1.846087, -1.244798,-0.01099), Point(1.846087, -0.833369,-0.01099)),
    #         Segment(Point( 1.846087, -0.377563,-0.01099), Point(1.846087, -0.729869,-0.01099)),
    #         Segment(Point( 1.846087, -0.833369,-0.01099), Point(1.846087, -0.729869,-0.01099)),
    #         Segment(Point(-1.846087, 1.846087,-0.01099), Point(0.182797, 1.846087,-0.01099)),
    #         Segment(Point( 0.182797, 1.846087,-0.01099), Point(0.42313, 1.846087,-0.01099)),
    #         Segment(Point( 1.846087, 1.846087,-0.01099), Point(1.507202, 1.846087,-0.01099)),
    #         Segment(Point( 0.42313, 1.846087,-0.01099), Point(0.713859, 1.846087,-0.01099)),
    #         Segment(Point( 1.507202, 1.846087,-0.01099), Point(0.713859, 1.846087,-0.01099)),
    #         Segment(Point( 1.846087, -2.076021,-0.01099), Point(-0.182797, -2.076021,-0.01099)),
    #         Segment(Point(-0.182797, -2.076021,-0.01099), Point(-0.521682, -2.076021,-0.01099)),
    #         Segment(Point(-1.846087, -2.076021,-0.01099), Point(-1.608179, -2.076021,-0.01099)),
    #         Segment(Point(-0.521682, -2.076021,-0.01099), Point(-1.315026, -2.076021,-0.01099)),
    #         Segment(Point(-1.608179, -2.076021,-0.01099), Point(-1.315026, -2.076021,-0.01099)),
    #         Segment(Point(-1.846087, -1.846087,-0.01099), Point(-1.846087, -1.972438,-0.01099)),
    #         Segment(Point(-1.846087, -1.972438,-0.01099), Point(-1.846087, -2.076021,-0.01099)),
    #         Segment(Point( 1.846087, -1.846087,-0.01099), Point(1.846087, -1.94967,-0.01099)),
    #         Segment(Point( 1.846087, -1.94967,-0.01099), Point(1.846087, -2.076021,-0.01099))
    #     ]
    #     result = surfaces_from_segments(segments)
    #     self.assertEqual(len(result), 1)
    #     self.assertEqual(len(result[0].poly.get_edges()), 4)

    def test_workflow_1(self):
        polygons = parse_stl("examples/cube.stl")
        self.assertEqual(len(polygons), 12)
        segments = []
        for p in polygons:
            segments += intersect_polygon_plane(p, 0)
        self.assertEqual(len(segments), 8)
        surfaces = surfaces_from_segments(segments)
        self.assertEqual(len(surfaces), 1)
        surf = surfaces[0]
        self.assertEqual(len(surf.points), 4)
        self.assertEqual(surf.fill, True)

    def test_workflow_2(self):
        polygons = parse_stl("examples/holed_cube.stl")
        self.assertEqual(len(polygons), 32)
        segments = []
        for p in polygons:
            segments += intersect_polygon_plane(p, 0)
        self.assertEqual(len(segments), 16)
        surfaces = surfaces_from_segments(segments)

        surf = surfaces[0]

        self.assertEqual(len(surf.points), 4)

        self.assertEqual(surf.points[0], Point(-1,1,0))
        self.assertEqual(surf.points[1], Point(1,1,0))
        self.assertEqual(surf.points[2], Point(1,-1,0))
        self.assertEqual(surf.points[3], Point(-1,-1,0))

        self.assertTrue(surf.fill)

        surf = surfaces[1]

        self.assertEqual(len(surf.points), 4)
        self.assertEqual(surf.points[0], Point(-0.278029,0.278029,0))
        self.assertEqual(surf.points[1], Point(0.278029,0.278029,0))
        self.assertEqual(surf.points[2], Point(0.278029,-0.278029,0))
        self.assertEqual(surf.points[3], Point(-0.278029,-0.278029,0))

        self.assertFalse(surf.fill)


def main():
    unittest.main()

main()