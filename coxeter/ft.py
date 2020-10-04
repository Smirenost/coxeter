"""Calculates Fourier transforms for form factors."""

import numpy as np
import rowan


class _FTbase:
    """Compute the Fourier transform of some function at some :math:`K` points.

    Attributes:
        FT (:class:`np.ndarray`): The Fourier transform.
    """

    def __init__(self, scale=1.0, density=1.0, k=None):
        self.scale = scale
        self.density = density
        self.S = np.zeros((0, 0), dtype=np.complex128)
        if k is not None:
            k = np.asarray(k)
            if k.shape[1] != 3:
                raise TypeError("K should be an Nx3 array")
        else:
            k = np.zeros((1, 3))
        self.K = k
        self.position = np.zeros((1, 3))
        self.orientation = np.zeros((1, 4))
        self.orientation[0][0] = 1.0

    def _compute_ft(self):
        pass

    def compute(self):
        self._compute_ft()
        return self

    def set_rq(self, position, orientation):
        """Set particle positions and orientations.

        Args:
            position ((:math:`N_{particles}`, 3) :class:`numpy.ndarray`):
                Particle position vectors.
            orientation ((:math:`N_{particles}`, 4) :class:`numpy.ndarray`):
                Particle orientation quaternions.
        """
        position = np.asarray(position)
        orientation = np.asarray(orientation)
        if position.shape[1] != 3:
            raise TypeError("position should be an Nx3 array")
        if orientation.shape[1] != 4:
            raise TypeError("orientation should be an Nx4 array")
        if position.shape[0] != orientation.shape[0]:
            raise TypeError("position and orientation should have the same length")

        self.position = position
        self.orientation = orientation


class FTdelta(_FTbase):
    """Compute the Fourier transform of a set of delta functions.

    Attributes:
        FT (:class:`np.ndarray`): The Fourier transform.
    """

    def __init__(self, density=1.0, k=None):
        super(FTdelta, self).__init__(density=density, k=k)

    def _compute_ft(self):
        self.S = np.zeros((len(self.K),), dtype=np.complex128)
        for i, k in enumerate(self.K):
            for r in self.position:
                self.S[i] += self.density * np.exp(-1j * np.dot(k, r))


class FTpolyhedron(_FTbase):
    """
    Generate the form factor of a polyhedron.

    Attributes:
        FT (:class:`np.ndarray`): The Fourier transform.
    """

    def __init__(self, scale=1.0, density=1.0, k=None):
        super(FTpolyhedron, self).__init__(scale=scale, density=density, k=k)

    def _compute_ft(self):
        self.S = np.zeros((len(self.K),), dtype=np.complex128)
        for i, k in enumerate(self.K):
            for r, q in zip(self.position, self.orientation):
                k_sq = np.dot(k, k)
                """
                The FT of an object with orientation q at a given k-space point
                is the same as the FT of the unrotated object at a k-space
                point rotated the opposite way. The opposite of the rotation
                represented by a quaternion is the conjugate of the quaternion,
                found by inverting the sign of the imaginary components.
                """
                k = rowan.rotate(rowan.inverse(q), k)
                f = 0
                if k_sq == 0:
                    f = self.volume
                else:
                    for face_id, face in enumerate(self.faces):
                        norm = self.norms[face_id]
                        k_dot_norm = np.dot(norm, k)
                        k_projected = k - k_dot_norm * norm
                        k_projected_sq = np.dot(k_projected, k_projected)
                        f2d = 0
                        if k_projected_sq == 0:
                            f2d = self.areas[face_id]
                        else:
                            n_verts = len(face)
                            for edge_id in range(n_verts):
                                r0 = self.verts[face[edge_id]]
                                r1 = self.verts[face[(edge_id + 1) % n_verts]]
                                edge_vec = r1 - r0
                                edge_center = 0.5 * (r0 + r1)
                                edge_cross_k = np.cross(edge_vec, k_projected)
                                k_dot_center = np.dot(k_projected, edge_center)
                                k_dot_edge = np.dot(k_projected, edge_vec)
                                # Note that np.sinc(x) gives sin(pi*x)/(pi*x)
                                f_n = (
                                    np.dot(norm, edge_cross_k)
                                    * np.sinc(0.5 * k_dot_edge / np.pi)
                                    / k_projected_sq
                                )
                                f2d -= f_n * 1j * np.exp(-1j * k_dot_center)
                        d = self.d[face_id]
                        exp_kr = np.exp(-1j * k_dot_norm * d)
                        f += k_dot_norm * (1j * f2d * exp_kr)
                    # end loop over faces
                    f /= k_sq
                # end if/else, f is now calculated
                # S += rho * f * exp(-i k r)
                self.S[i] += (
                    self.density
                    * f
                    * np.exp(-1j * np.dot(k, rowan.rotate(rowan.inverse(q), r)))
                )

    def set_params(self, verts, faces, norms, d, areas, volume):
        """Set polyhedron geometry.

        Args:
            verts ((:math:`N_{particles}`, 3) :class:`numpy.ndarray`):
                Vertex coordinates.
            faces ((:math:`N_{faces}`, 3) :class:`numpy.ndarray`):
                Facet vertex indices.
            norms ((:math:`N_{faces}`, 3) :class:`numpy.ndarray`):
                Facet normals.
            d ((:math:`N_{faces}`) :class:`numpy.ndarray`):
                Facet distances.
            area ((:math:`N_{faces}`) :class:`numpy.ndarray`):
                Facet areas.
            volume (:class:`numpy.float64`):
                Polyhedron volume.
        """
        verts = np.asarray(verts)
        if verts.shape[1] != 3:
            raise TypeError("verts should be an Nx3 array")

        face_offs = np.zeros((len(faces) + 1), dtype=np.uint32)
        for i, f in enumerate(faces):
            face_offs[i + 1] = face_offs[i] + len(f)

        face_offs = np.asarray(face_offs)

        faces = np.asarray(faces)

        norms = np.asarray(norms)
        if norms.shape[1] != 3:
            raise TypeError("norms should be an Nx3 array")

        d = np.asarray(d)

        areas = np.asarray(areas)

        if norms.shape[0] != face_offs.shape[0] - 1:
            raise RuntimeError(
                ("Length of norms should be equal to number of face offsets" "- 1")
            )
        if d.shape[0] != face_offs.shape[0] - 1:
            raise RuntimeError(
                (
                    "Length of face distances should be equal to number of face"
                    "offsets - 1"
                )
            )
        if areas.shape[0] != face_offs.shape[0] - 1:
            raise RuntimeError(
                ("Length of areas should be equal to number of face offsets" "- 1")
            )
        self.verts = verts
        self.face_offs = face_offs
        self.faces = faces
        self.norms = norms
        self.d = d
        self.areas = areas
        self.volume = volume


class FTconvexPolyhedron(FTpolyhedron):
    """Fourier Transform for convex polyhedra.

    Args:
        hull (:class:`coxeter.shape_classes.ConvexPolyhedron`):
            Convex polyhedron object.
    """

    def __init__(self, hull, scale=1.0, density=1.0, k=None):
        super(FTconvexPolyhedron, self).__init__(scale=scale, density=density, k=k)
        self.hull = hull

        # set convex hull geometry
        verts = self.hull.vertices * self.scale
        faces = self.hull.faces
        norms = self.hull._equations[:, 0:3]
        d = -self.hull._equations[:, 3] * self.scale
        areas = [
            self.hull.get_face_area(i) * self.scale ** 2.0 for i in range(len(faces))
        ]
        volume = self.hull.volume * self.scale ** 3.0
        self.set_params(verts, faces, norms, d, areas, volume)

    def spoly_2d(self, i, k):
        r"""Calculate Fourier transform of polygon.

        Args:
            i (float):
                Face index into self.hull simplex list.
            k (:class:`numpy.ndarray`):
                Angular wave vector at which to calculate
                :math:`S\left(i\right)`.
        """
        if np.dot(k, k) == 0.0:
            ft = self.hull.getArea(i) * self.scale ** 2
        else:
            ft = 0.0
            nverts = self.hull.nverts[i]
            verts = list(self.hull.faces[i, 0:nverts])
            # apply periodic boundary condition for convenience
            verts.append(verts[0])
            points = self.hull.points * self.scale
            n = self.hull.equations[i, 0:3]
            for j in range(self.hull.nverts[i]):
                v1 = points[verts[j + 1]]
                v0 = points[verts[j]]
                edge = v1 - v0
                centrum = np.array((v1 + v0) / 2.0)
                # Note that np.sinc(x) gives sin(pi*x)/(pi*x)
                x = np.dot(k, edge) / np.pi
                cpedgek = np.cross(edge, k)
                ft += (
                    np.dot(n, cpedgek) * np.exp(-1.0j * np.dot(k, centrum)) * np.sinc(x)
                )
            ft *= -1.0j / np.dot(k, k)
        return ft

    def spoly_3d(self, k):
        r"""Calculate Fourier transform of polyhedron.

        Args:
            k (:class:`numpy.ndarray`):
                Angular wave vector at which to calculate
                :math:`S\left(i\right)`.
        """
        if np.dot(k, k) == 0.0:
            ft = self.hull.getVolume() * self.scale ** 3
        else:
            ft = 0.0
            # for face in faces
            for i in range(self.hull.nfaces):
                # need to project k into plane of face
                ni = self.hull.equations[i, 0:3]
                di = -self.hull.equations[i, 3] * self.scale
                dotkni = np.dot(k, ni)
                k_proj = k - ni * dotkni
                ft += dotkni * np.exp(-1.0j * dotkni * di) * self.spoly_2d(i, k_proj)
            ft *= 1.0j / (np.dot(k, k))
        return ft
