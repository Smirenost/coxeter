from __future__ import division
from numpy import sqrt
import numpy
from euclid.FreudShape import ConvexPolyhedron

# Example:
# from euclid.FreudShape.TriangularPrism import shape
points = [ 
          (-1/(2*sqrt(3)), -1/2, -1/2),
          (-1/(2*sqrt(3)), -1/2, 1/2),
          (-1/(2*sqrt(3)), 1/2, -1/2),
          (-1/(2*sqrt(3)), 1/2, 1/2),
          (1/sqrt(3), 0, -1/2),
          (1/sqrt(3), 0, 1/2),
         ]

shape = ConvexPolyhedron(numpy.array(points))
