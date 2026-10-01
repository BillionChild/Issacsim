"""Conservative boxes and robot-triangle/cube narrow phase; no physics."""
import numpy as np
from pxr import UsdGeom

def box(local, matrix):
    corners = local @ matrix[:3, :3] + matrix[3, :3]
    axes = matrix[:3, :3].copy()
    axes /= np.linalg.norm(axes, axis=1)[:, None]
    center = corners.mean(axis=0)
    half = np.max(np.abs((corners-center) @ axes.T), axis=0)
    return corners.min(axis=0), corners.max(axis=0), center, axes, half


def overlap(a, b):
    if np.any(np.minimum(a[1], b[1])-np.maximum(a[0], b[0]) <= .0005):
        return False
    delta = b[2]-a[2]
    for axis in list(a[3])+list(b[3])+[np.cross(x, y) for x in a[3] for y in b[3]]:
        norm = np.linalg.norm(axis)
        if norm < 1e-8:
            continue
        axis = axis/norm
        ra = np.sum(a[4]*np.abs(a[3]@axis))
        rb = np.sum(b[4]*np.abs(b[3]@axis))
        if abs(delta@axis) >= ra+rb-.0005:
            return False
    return True


def mesh_cube_overlap(mesh, cube, cache):
    """Triangle/AABB SAT in cube-local space, after conservative OBB broad phase."""
    matrix = np.array(cache.GetLocalToWorldTransform(mesh)) @ np.linalg.inv(np.array(cache.GetLocalToWorldTransform(cube)))
    points = np.array(UsdGeom.Mesh(mesh).GetPointsAttr().Get())
    vertices = points @ matrix[:3,:3]+matrix[3,:3]
    geom = UsdGeom.Mesh(mesh)
    counts = np.array(geom.GetFaceVertexCountsAttr().Get())
    assert np.all(counts == 3), 'Narrow phase expects converted triangular robot meshes'
    triangles = vertices[np.array(geom.GetFaceVertexIndicesAttr().Get()).reshape(-1,3)]
    half = float(UsdGeom.Cube(cube).GetSizeAttr().Get())/2
    keep = np.all(triangles.min(axis=1) <= half,axis=1) & np.all(triangles.max(axis=1) >= -half,axis=1)
    triangles = triangles[keep]
    if not len(triangles): return False
    edges = [triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,1],triangles[:,0]-triangles[:,2]]
    axes = [np.cross(edges[0],edges[1])]+[np.cross(edge,basis) for edge in edges for basis in np.eye(3)]
    active = np.ones(len(triangles),dtype=bool)
    for axis in axes:
        values = np.einsum('nij,nj->ni',triangles,axis)
        radius = half*np.abs(axis).sum(axis=1)
        active &= (values.min(axis=1) <= radius+1e-8) & (values.max(axis=1) >= -radius-1e-8)
    return bool(np.any(active))
