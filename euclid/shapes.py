# For calling up commonly used shapes
from . import np
from . import ConvexHull
from . import utils

# Base class for shapes. It really doesn't work for 2D stuff yet
class Shape(object):

    # The IDstr is a string identifier. Can be a name or
    # a numerical designation. 'Content' is a dimension
    # agnostic way to say 'volume' or 'area'
    def __init__(self, vertices, radius=0, content=None):
        self.ndims = vertices.shape[1]
        self.radius = radius

        if self.radius > 0:
            self.is_sphero = True
        else:
            self.is_sphero = False


        # Change the volume of the shape
        if content is not None:
            self.content = self.normalizeContent(self, vertices, content)
        else:
            self.content = self.git Content(self, vertices)
        else:
            self.verts = np.asarray(vertices)
            if self.is_sphero:
                self.content = utils.spheropolyhedra_volume(vertices, R=radius)
            else:
                self.content = ConvexHull(vertices).volume()


        self.hull = ConvexHull(vertices)

    # A function for normalizing the content of a shape
    def normalizeContent(self, vertices, content):
        vol = self.getContent(self, vertices)
        self.content = content
        self.vertices = vertices/np.power(vol,1/self.ndims)

        return None


    # a function for finding the content of a shape
    def getContent(self, vertices):
        if self.is_sphero:
            vol = utils.spheropolyhedra_volume(vertices, R=radius)
        else:
            vol = ConvexHull(vertices).volume()

        return vol


# Truncation ranges from 0 (octahedra) to 2/3 (truncated octahedra) to 1 (cuboctahedra)
def octahedron(side_length = 1, truncation = 0):
	pre = np.sqrt(2)/2
	if truncation:

		trunc_value = truncation*np.sqrt(2)*side_length/4

		return np.asarray([[pre*side_length-trunc_value,trunc_value,0],
                         [pre*side_length-trunc_value,-trunc_value,0],
                         [pre*side_length-trunc_value,0,trunc_value],
                         [pre*side_length-trunc_value,0,-trunc_value],
                         [-pre*side_length+trunc_value,trunc_value,0],
                         [-pre*side_length+trunc_value,-trunc_value,0],
                         [-pre*side_length+trunc_value,0,trunc_value],
                         [-pre*side_length+trunc_value,0,-trunc_value],
                         [0,pre*side_length-trunc_value,trunc_value],
                         [0,pre*side_length-trunc_value,-trunc_value],
                         [trunc_value,pre*side_length-trunc_value,0],
                         [-trunc_value,pre*side_length-trunc_value,0],
                         [0,-pre*side_length+trunc_value,trunc_value],
                         [0,-pre*side_length+trunc_value,-trunc_value],
                         [trunc_value,-pre*side_length+trunc_value,0],
                         [-trunc_value,-pre*side_length+trunc_value,0],
                         [0,trunc_value,pre*side_length-trunc_value],
                         [0,-trunc_value,pre*side_length-trunc_value],
                         [trunc_value,0,pre*side_length-trunc_value],
                         [-trunc_value,0,pre*side_length-trunc_value],
                         [0,trunc_value,-pre*side_length+trunc_value],
                         [0,-trunc_value,-pre*side_length+trunc_value],
                         [trunc_value,0,-pre*side_length+trunc_value],
                         [-trunc_value,0,-pre*side_length+trunc_value]])
	else:
		return np.asarray([[pre*side_length,0,0],[-pre*side_length,0,0],[0,pre*side_length,0],
                         [0,-pre*side_length,0],[0,0,pre*side_length],[0,0,-pre*side_length]])

def cube(side_length = 1):
	return np.asarray([[side_length/2,side_length/2,side_length/2],
		[-side_length/2,side_length/2,side_length/2],
		[side_length/2,-side_length/2,side_length/2],
		[side_length/2,side_length/2,-side_length/2],
		[-side_length/2,-side_length/2,side_length/2],
		[-side_length/2,side_length/2,-side_length/2],
		[side_length/2,-side_length/2,-side_length/2],
		[-side_length/2,-side_length/2,-side_length/2]])

def rectangle(a, b, c):
	return np.asarray([[a/2,b/2,c/2],
		[-a/2,b/2,c/2],
		[a/2,-b/2,c/2],
		[a/2,b/2,-c/2],
		[-a/2,-b/2,c/2],
		[-a/2,b/2,-c/2],
		[a/2,-b/2,-c/2],
		[-a/2,-b/2,-c/2]])

# This golden spiral code snippet is taken from http://www.softimageblog.com/archives/115
def poly_sphere(radius = 1, points = 100):
	stype = 'polyedral sphere'
	pts = []
	inc = np.pi*(3 - np.sqrt(5))
	off = 2/float(points)
	for k in range(0, int(points)):
		y = k*off - 1 + (off/2)
		r = np.sqrt(1 - y*y)
		phi = k*inc
		pts.append([np.cos(phi)*r, y, np.sin(phi)*r])
	return radius*np.array(pts)

def rhombic_dodecahedron(a = 1):
	return np.array([[a,a,a],[-a,a,a],[a,-a,a],
                     [a,a,-a],[a,-a,-a],[-a,a,-a],
                     [-a,-a,a],[-a,-a,-a],[2.0*a,0.0,0.0],
                     [-2.0*a,0.0,0.0],[0.0,2.0*a,0.0],[0.0,-2.0*a,0.0],
                     [0.0,0.0,2.0*a],[0.0,0.0,-2.0*a]])

