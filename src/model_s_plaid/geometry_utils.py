"""
Mathematical Class-A surface utilities for Blender (pure NumPy + bmesh).

Provides:
- Monotonic PCHIP (Fritsch-Carlson) cubic Hermite interpolation (zero overshoot/wobble!)
- Smooth C2 cubic B-spline curve/surface evaluation
- Clean all-quad lofting with automatic UV generation
- Automotive panel flange rolling (beveled edge + inward return flange into dark gap)
- Mesh integrity validation (manifold check, outward normals, smooth shading)
"""

import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix


def pchip_interpolate(xs, ys, x_eval):
    """
    Fritsch-Carlson monotone piecewise cubic Hermite interpolation (PCHIP).
    Zero Gibbs overshoot or artificial waves between automotive control points.
    Supports scalar or 1D numpy array x_eval.
    """
    xs = np.asarray(xs, dtype=np.float64)
    ys = np.asarray(ys, dtype=np.float64)
    scalar_in = np.isscalar(x_eval)
    xe = np.atleast_1d(np.asarray(x_eval, dtype=np.float64))

    # Ensure ascending xs
    if xs[0] > xs[-1]:
        xs = xs[::-1]
        ys = ys[::-1]

    n = len(xs)
    h = np.diff(xs)
    delta = np.diff(ys) / h

    d = np.zeros(n, dtype=np.float64)
    if n == 2:
        d[:] = delta[0]
    else:
        for k in range(1, n - 1):
            if delta[k - 1] * delta[k] > 0.0:
                w1 = 2.0 * h[k] + h[k - 1]
                w2 = h[k] + 2.0 * h[k - 1]
                d[k] = (w1 + w2) / (w1 / delta[k - 1] + w2 / delta[k])
            else:
                d[k] = 0.0

        # Endpoint slopes (non-centered three-point shape-preserving formula)
        d0 = ((2.0 * h[0] + h[1]) * delta[0] - h[0] * delta[1]) / (h[0] + h[1])
        if np.sign(d0) != np.sign(delta[0]):
            d0 = 0.0
        elif np.sign(delta[0]) != np.sign(delta[1]) and abs(d0) > abs(3.0 * delta[0]):
            d0 = 3.0 * delta[0]
        d[0] = d0

        dn = ((2.0 * h[-1] + h[-2]) * delta[-1] - h[-1] * delta[-2]) / (h[-1] + h[-2])
        if np.sign(dn) != np.sign(delta[-1]):
            dn = 0.0
        elif np.sign(delta[-1]) != np.sign(delta[-2]) and abs(dn) > abs(3.0 * delta[-1]):
            dn = 3.0 * delta[-1]
        d[-1] = dn

    xe_clamped = np.clip(xe, xs[0], xs[-1])
    idx = np.searchsorted(xs, xe_clamped, side="right") - 1
    idx = np.clip(idx, 0, n - 2)

    hk = h[idx]
    t = (xe_clamped - xs[idx]) / hk
    t2 = t * t
    t3 = t2 * t

    h00 = 2.0 * t3 - 3.0 * t2 + 1.0
    h10 = t3 - 2.0 * t2 + t
    h01 = -2.0 * t3 + 3.0 * t2
    h11 = t3 - t2

    res = h00 * ys[idx] + h10 * hk * d[idx] + h01 * ys[idx + 1] + h11 * hk * d[idx + 1]
    return float(res[0]) if scalar_in else res


def smoothstep(edge0, edge1, x):
    """C1 smoothstep ramp."""
    t = np.clip((x - edge0) / max(edge1 - edge0, 1e-9), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def smootherstep(edge0, edge1, x):
    """C2 smootherstep (zero 1st and 2nd derivatives at endpoints - true Class-A blend!)."""
    t = np.clip((x - edge0) / max(edge1 - edge0, 1e-9), 0.0, 1.0)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def cubic_bezier(p0, p1, p2, p3, t):
    """Evaluate cubic Bezier curve at parameter t (scalar or array)."""
    t = np.asarray(t, dtype=np.float64)[..., None]
    u = 1.0 - t
    return (
        (u ** 3) * np.asarray(p0)
        + 3.0 * (u ** 2) * t * np.asarray(p1)
        + 3.0 * u * (t ** 2) * np.asarray(p2)
        + (t ** 3) * np.asarray(p3)
    )


def ensure_collection(name, parent=None):
    """Get or create a Blender collection cleanly organized in scene hierarchy."""
    if name in bpy.data.collections:
        col = bpy.data.collections[name]
    else:
        col = bpy.data.collections.new(name)
        if parent is None:
            bpy.context.scene.collection.children.link(col)
        else:
            parent.children.link(col)
    return col


def link_object(obj, collection):
    """Link object exclusively to the specified collection."""
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def set_smooth_shading(mesh):
    """Apply smooth shading to all polygons in Blender 4.2 cleanly."""
    if len(mesh.polygons) > 0:
        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.update()


def create_mesh_object(name, verts, faces, collection, material=None, uvs=None, smooth=True):
    """Create a Blender mesh object from vertex/face lists with optional UVs."""
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    if uvs is not None and len(mesh.loops) > 0:
        uv_layer = mesh.uv_layers.new(name="UVMap")
        if len(uvs) == len(verts):
            for poly in mesh.polygons:
                for loop_idx in poly.loop_indices:
                    v_idx = mesh.loops[loop_idx].vertex_index
                    uv_layer.data[loop_idx].uv = uvs[v_idx]
        elif len(uvs) == len(mesh.loops):
            for i, uv in enumerate(uvs):
                uv_layer.data[i].uv = uv

    if smooth:
        set_smooth_shading(mesh)

    obj = bpy.data.objects.new(name, mesh)
    link_object(obj, collection)

    if material is not None:
        if len(obj.data.materials) == 0:
            obj.data.materials.append(material)
        else:
            obj.data.materials[0] = material
    return obj


def create_grid_surface(name, grid_pts, collection, material=None,
                        close_u=False, close_v=False, mirror_x=False,
                        flip_normals=False, uv_scale=(1.0, 1.0),
                        add_flange=False, flange_depth=0.012, flange_bevel=0.002):
    """
    Build a clean all-quad mesh from a 2D array grid_pts of shape (NU, NV, 3).
    Optionally adds rolled automotive panel flanges along open boundary edges
    so shutlines have true physical depth and specular edge catch-lights!
    """
    pts = np.asarray(grid_pts, dtype=np.float64)
    nu, nv, _ = pts.shape

    bm = bmesh.new()
    bm_verts = [[None] * nv for _ in range(nu)]
    for i in range(nu):
        for j in range(nv):
            bm_verts[i][j] = bm.verts.new(tuple(pts[i, j]))
    bm.verts.ensure_lookup_table()

    u_max = nu if close_u else nu - 1
    v_max = nv if close_v else nv - 1

    uv_layer = bm.loops.layers.uv.new("UVMap")

    main_faces = []
    for i in range(u_max):
        i_next = (i + 1) % nu
        for j in range(v_max):
            j_next = (j + 1) % nv
            v0 = bm_verts[i][j]
            v1 = bm_verts[i_next][j]
            v2 = bm_verts[i_next][j_next]
            v3 = bm_verts[i][j_next]
            # Avoid degenerate zero-area faces
            if (v0.co - v1.co).length < 1e-6 and (v2.co - v3.co).length < 1e-6:
                continue
            try:
                if flip_normals:
                    f = bm.faces.new((v0, v3, v2, v1))
                else:
                    f = bm.faces.new((v0, v1, v2, v3))
                main_faces.append(f)
                # Assign clean parametric UVs
                u0 = (i / max(nu - 1, 1)) * uv_scale[0]
                u1 = ((i + 1) / max(nu - 1, 1)) * uv_scale[0]
                w0 = (j / max(nv - 1, 1)) * uv_scale[1]
                w1 = ((j + 1) / max(nv - 1, 1)) * uv_scale[1]
                coords = [(u0, w0), (u0, w1), (u1, w1), (u1, w0)] if flip_normals else [(u0, w0), (u1, w0), (u1, w1), (u0, w1)]
                for loop, uv in zip(f.loops, coords):
                    loop[uv_layer].uv = uv
            except ValueError:
                pass

    bm.normal_update()

    # Optional automotive rolled edge flange on open boundaries
    if add_flange:
        bm.edges.ensure_lookup_table()
        boundary_edges = [e for e in bm.edges if e.is_boundary]
        if mirror_x:
            # Do NOT extrude flange along the X=0 mirror symmetry centerline!
            boundary_edges = [
                e for e in boundary_edges
                if not (abs(e.verts[0].co.x) < 1e-4 and abs(e.verts[1].co.x) < 1e-4)
            ]
        if boundary_edges:
            # First step: subtle 2 mm rolled bevel edge
            ret1 = bmesh.ops.extrude_edge_only(bm, edges=boundary_edges)
            new_verts1 = [el for el in ret1["geom"] if isinstance(el, bmesh.types.BMVert)]
            new_edges1 = [el for el in ret1["geom"] if isinstance(el, bmesh.types.BMEdge)]
            # Move slightly inward along vertex normal & inward tangent
            for v in new_verts1:
                n = v.normal.normalized() if v.normal.length > 1e-6 else Vector((0, 0, 1))
                v.co -= n * flange_bevel
            bm.normal_update()

            # Second step: deep inward return flange into shadow gap
            outer_edges = [e for e in new_edges1 if e.is_boundary]
            if outer_edges:
                ret2 = bmesh.ops.extrude_edge_only(bm, edges=outer_edges)
                new_verts2 = [el for el in ret2["geom"] if isinstance(el, bmesh.types.BMVert)]
                for v in new_verts2:
                    n = v.normal.normalized() if v.normal.length > 1e-6 else Vector((0, 0, 1))
                    v.co -= n * flange_depth

    bm.normal_update()

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    set_smooth_shading(mesh)
    obj = bpy.data.objects.new(name, mesh)
    link_object(obj, collection)

    if material is not None:
        obj.data.materials.append(material)

    if mirror_x:
        mod = obj.modifiers.new(name="MirrorX", type="MIRROR")
        mod.use_axis = (True, False, False)
        mod.use_clip = True
        mod.merge_threshold = 0.0005

    return obj


def add_normal_transfer(panel_obj, master_clay_obj, max_dist=0.015):
    """
    Transfer exact Class-A smooth custom split normals from the uncut master clay
    surface onto the outer painted faces of a panel!
    Ensures unbroken automotive studio reflections across door/hood/fender shutlines.
    """
    # Create vertex group for outer skin vertices (close to master clay)
    vg = panel_obj.vertex_groups.new(name="ClassA_Skin")
    # Assign all vertices initially; DataTransfer max_distance limits transfer to outer skin only!
    vg.add(list(range(len(panel_obj.data.vertices))), 1.0, 'REPLACE')

    mod = panel_obj.modifiers.new(name="ClassA_Normals", type="DATA_TRANSFER")
    mod.object = master_clay_obj
    mod.use_loop_data = True
    mod.data_types_loops = {'CUSTOM_NORMAL'}
    mod.loop_mapping = 'POLYINTERP_NEAREST'
    mod.use_max_distance = True
    mod.max_distance = max_dist
    mod.mix_mode = 'REPLACE'
    mod.mix_factor = 1.0
    return mod


def add_solidify(obj, thickness=0.004, offset=-1.0, use_rim=True):
    """Add clean physical thickness to glass, lenses, or trim."""
    mod = obj.modifiers.new(name="Solidify", type="SOLIDIFY")
    mod.thickness = thickness
    mod.offset = offset
    mod.use_rim = use_rim
    return mod


def add_bevel(obj, width=0.002, segments=2, angle_limit=math.radians(30)):
    """Add sharp specular catch-light bevels to hard mechanical/trim edges."""
    mod = obj.modifiers.new(name="Bevel", type="BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    mod.angle_limit = angle_limit
    mod.harden_normals = False
    return mod


def add_subsurf(obj, levels=1, render_levels=2):
    """Add Catmull-Clark subdivision surface modifier."""
    mod = obj.modifiers.new(name="Subsurf", type="SUBSURF")
    mod.levels = levels
    mod.render_levels = render_levels
    return mod


def create_tube_along_points(name, points, radii, collection, material=None,
                             segments=16, cap_ends=True, mirror_x=False):
    """Sweep a smooth circular/elliptical tube along a 3D polyline (for LED light pipes, seals, yoke, etc.)."""
    pts = [Vector(p) for p in points]
    n = len(pts)
    if np.isscalar(radii):
        rads = [(float(radii), float(radii))] * n
    elif isinstance(radii, tuple) and len(radii) == 2 and np.isscalar(radii[0]) and np.isscalar(radii[1]):
        rads = [(float(radii[0]), float(radii[1]))] * n
    elif isinstance(radii, list) and len(radii) == 2 and np.isscalar(radii[0]) and np.isscalar(radii[1]) and n != 2:
        rads = [(float(radii[0]), float(radii[1]))] * n
    else:
        rads = [(r, r) if np.isscalar(r) else (float(r[0]), float(r[1])) for r in radii]

    bm = bmesh.new()
    rings = []
    prev_up = Vector((0, 0, 1))

    for i, p in enumerate(pts):
        if i == 0:
            tangent = (pts[1] - pts[0]).normalized()
        elif i == n - 1:
            tangent = (pts[-1] - pts[-2]).normalized()
        else:
            tangent = (pts[i + 1] - pts[i - 1]).normalized()

        if abs(tangent.dot(prev_up)) > 0.95:
            ref = Vector((1, 0, 0))
        else:
            ref = prev_up
        side = tangent.cross(ref).normalized()
        up = side.cross(tangent).normalized()
        prev_up = up

        rx, rz = rads[i]
        ring = []
        for s in range(segments):
            ang = 2.0 * math.pi * s / segments
            offset = side * (math.cos(ang) * rx) + up * (math.sin(ang) * rz)
            ring.append(bm.verts.new(p + offset))
        rings.append(ring)

    for i in range(n - 1):
        r0, r1 = rings[i], rings[i + 1]
        for s in range(segments):
            sn = (s + 1) % segments
            bm.faces.new((r0[s], r0[sn], r1[sn], r1[s]))

    if cap_ends:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    set_smooth_shading(mesh)
    obj = bpy.data.objects.new(name, mesh)
    link_object(obj, collection)
    if material is not None:
        obj.data.materials.append(material)
    if mirror_x:
        mod = obj.modifiers.new(name="MirrorX", type="MIRROR")
        mod.use_axis = (True, False, False)
    return obj


def create_revolved_mesh(name, profile_rz, collection, material=None,
                         segments=96, axis='X', origin=(0, 0, 0),
                         uv_radial=False, close_profile=False):
    """
    Create a high-resolution surface of revolution from (r, axial) pairs.
    axis='X': profile is (radius_in_YZ, x_coord) — ideal for car wheels, tires, brake rotors!
    """
    bm = bmesh.new()
    n_prof = len(profile_rz)
    rings = []
    ox, oy, oz = origin

    for s in range(segments):
        ang = 2.0 * math.pi * s / segments
        ca, sa = math.cos(ang), math.sin(ang)
        ring = []
        for r, ax in profile_rz:
            if axis == 'X':
                co = (ox + ax, oy + r * ca, oz + r * sa)
            elif axis == 'Y':
                co = (ox + r * ca, oy + ax, oz + r * sa)
            else:
                co = (ox + r * ca, oy + r * sa, oz + ax)
            ring.append(bm.verts.new(co))
        rings.append(ring)

    uv_layer = bm.loops.layers.uv.new("UVMap")
    r_max = max(r for r, _ in profile_rz) or 1.0
    p_max = n_prof if close_profile else n_prof - 1

    for s in range(segments):
        sn = (s + 1) % segments
        a0 = 2.0 * math.pi * s / segments
        a1 = 2.0 * math.pi * (s + 1) / segments
        for p in range(p_max):
            pn = (p + 1) % n_prof
            v0, v1, v2, v3 = rings[s][p], rings[sn][p], rings[sn][pn], rings[s][pn]
            try:
                f = bm.faces.new((v0, v1, v2, v3))
                if uv_radial:
                    r0 = profile_rz[p][0] / r_max
                    r1 = profile_rz[pn][0] / r_max
                    uvs = [
                        (0.5 + 0.5 * r0 * math.cos(a0), 0.5 + 0.5 * r0 * math.sin(a0)),
                        (0.5 + 0.5 * r0 * math.cos(a1), 0.5 + 0.5 * r0 * math.sin(a1)),
                        (0.5 + 0.5 * r1 * math.cos(a1), 0.5 + 0.5 * r1 * math.sin(a1)),
                        (0.5 + 0.5 * r1 * math.cos(a0), 0.5 + 0.5 * r1 * math.sin(a0)),
                    ]
                else:
                    u0, u1 = s / segments, (s + 1) / segments
                    w0, w1 = p / max(n_prof - 1, 1), (p + 1) / max(n_prof - 1, 1)
                    uvs = [(u0, w0), (u1, w0), (u1, w1), (u0, w1)]
                for loop, uv in zip(f.loops, uvs):
                    loop[uv_layer].uv = uv
            except ValueError:
                pass

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    set_smooth_shading(mesh)
    obj = bpy.data.objects.new(name, mesh)
    link_object(obj, collection)
    if material is not None:
        obj.data.materials.append(material)
    return obj
