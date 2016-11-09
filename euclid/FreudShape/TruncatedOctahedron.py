from __future__ import division
from numpy import sqrt
import numpy
from euclid.FreudShape import ConvexPolyhedron

# Example:
# from euclid.FreudShape.TruncatedOctahedron import shape as truncOct

points = [  [-(3/2), -(1/2), 0],
            [-(3/2), 1/2, 0],
            [-1, -1, -(1/sqrt(2))],
            [-1, -1, 1/sqrt(2)],
            [-1, 1, -(1/sqrt(2))],
            [-1, 1, 1/sqrt(2)],
            [-(1/2), -(3/2), 0],
            [-(1/2), -(1/2), -sqrt(2)],
            [-(1/2), -(1/2), sqrt(2)],
            [-(1/2), 1/2, -sqrt(2)],
            [-(1/2), 1/2, sqrt(2)],
            [-(1/2), 3/2, 0],
            [1/ 2, -(3/2), 0],
            [1/2, -(1/2), -sqrt(2)],
            [1/2, -(1/2), sqrt(2)],
            [1/ 2, 1/2, -sqrt(2)],
            [1/2, 1/2, sqrt(2)],
            [1/2, 3/2, 0],
            [1, -1, -(1/sqrt(2))],
            [1, -1, 1/sqrt(2)],
            [1, 1, -(1/sqrt(2))],
            [1, 1, 1/sqrt(2)],
            [3/2, -(1/2), 0],
            [3/2, 1/2, 0]
        ]

shape = ConvexPolyhedron(numpy.array(points))

