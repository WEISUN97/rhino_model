import math

import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc

LAYER_NAME = "GeneratedGeometry"


def _is_object_list(value):
    return isinstance(value, (list, tuple))


def _map_objects(object_ids, operation):
    """Apply an operation to one object ID or each ID in a list/tuple."""
    if _is_object_list(object_ids):
        return [operation(object_id) for object_id in object_ids]
    return operation(object_ids)


def begin_model():
    """Prepare the generated-geometry layer for a new model."""
    if not rs.IsLayer(LAYER_NAME):
        rs.AddLayer(LAYER_NAME)

    object_ids = rs.ObjectsByLayer(LAYER_NAME, select=False)
    if object_ids:
        rs.DeleteObjects(object_ids)

    return LAYER_NAME


def finish_model():
    """Refresh Rhino after the model has been rebuilt."""
    sc.doc.Views.Redraw()


def add_to_layer(object_ids, layer_name=LAYER_NAME):
    """Add one object ID or a list of IDs to a Rhino layer."""
    if _is_object_list(object_ids):
        return [add_to_layer(object_id, layer_name) for object_id in object_ids]
    object_id = object_ids
    if object_id:
        rs.ObjectLayer(object_id, layer_name)
    return object_id


def delete_object(object_ids):
    """Delete one object ID or a list of IDs and return deletion status."""
    return _map_objects(object_ids, lambda object_id: sc.doc.Objects.Delete(object_id, True))


def delete_objects(object_ids):
    """Delete multiple document objects and return the IDs deleted successfully."""
    return [object_id for object_id in object_ids if delete_object(object_id)]


def create_point(x, y, z):
    point = Rhino.Geometry.Point3d(x, y, z)
    return sc.doc.Objects.AddPoint(point)


def create_line(start, end):
    start_pt = Rhino.Geometry.Point3d(*start)
    end_pt = Rhino.Geometry.Point3d(*end)
    return sc.doc.Objects.AddLine(start_pt, end_pt)


def create_rectangle(origin, width, height):
    plane = Rhino.Geometry.Plane(
        Rhino.Geometry.Point3d(*origin), Rhino.Geometry.Vector3d.ZAxis
    )
    rectangle = Rhino.Geometry.Rectangle3d(plane, width, height)
    return sc.doc.Objects.AddPolyline(rectangle.ToPolyline())


def create_circle(center, radius):
    circle = Rhino.Geometry.Circle(Rhino.Geometry.Point3d(*center), radius)
    return sc.doc.Objects.AddCircle(circle)


# origin is the bottom-left corner of the box.
def create_box(length, width, height, origin=(0.0, 0.0, 0.0)):
    plane = Rhino.Geometry.Plane(
        Rhino.Geometry.Point3d(*origin), Rhino.Geometry.Vector3d.ZAxis
    )
    box = Rhino.Geometry.Box(
        plane,
        Rhino.Geometry.Interval(0.0, length),
        Rhino.Geometry.Interval(0.0, width),
        Rhino.Geometry.Interval(0.0, height),
    )
    return sc.doc.Objects.AddBrep(box.ToBrep())


def create_sphere(radius, center=(0.0, 0.0, 0.0)):
    sphere = Rhino.Geometry.Sphere(Rhino.Geometry.Point3d(*center), radius)
    return sc.doc.Objects.AddSphere(sphere)


def create_cylinder(radius, height, center=(0.0, 0.0, 0.0)):
    plane = Rhino.Geometry.Plane(
        Rhino.Geometry.Point3d(*center), Rhino.Geometry.Vector3d.ZAxis
    )
    cylinder = Rhino.Geometry.Cylinder(Rhino.Geometry.Circle(plane, radius), height)
    return sc.doc.Objects.AddBrep(cylinder.ToBrep(True, True))


def _find_object(object_id):
    rhino_object = sc.doc.Objects.FindId(object_id)
    if not rhino_object:
        raise ValueError("Rhino object was not found: {0}".format(object_id))
    return rhino_object


def _point3d(value):
    return Rhino.Geometry.Point3d(*value)


def _transform_object(object_id, transform, copy):
    result_id = sc.doc.Objects.Transform(object_id, transform, not copy)
    if not result_id:
        raise RuntimeError("Rhino could not transform object: {0}".format(object_id))
    return result_id


def _breps_from_ids(object_ids):
    breps = []
    for object_id in object_ids:
        geometry = _find_object(object_id).Geometry
        if not isinstance(geometry, Rhino.Geometry.Brep):
            raise ValueError("Boolean operations require Brep object IDs.")
        breps.append(geometry)
    return breps


def _add_boolean_results(breps, source_id, input_ids, delete_input):
    if not breps:
        return []

    attributes = _find_object(source_id).Attributes.Duplicate()
    result_ids = [sc.doc.Objects.AddBrep(brep, attributes) for brep in breps]

    if delete_input:
        for object_id in input_ids:
            sc.doc.Objects.Delete(object_id, True)

    return result_ids


def boolean_union(object_ids, delete_input=True):
    """Union Brep objects and return IDs for the resulting Breps."""
    input_ids = list(object_ids)
    if len(input_ids) < 2:
        raise ValueError("boolean_union requires at least two object IDs.")

    breps = _breps_from_ids(input_ids)
    tolerance = sc.doc.ModelAbsoluteTolerance
    results = Rhino.Geometry.Brep.CreateBooleanUnion(breps, tolerance)
    return _add_boolean_results(results, input_ids[0], input_ids, delete_input)


def boolean_difference(base_ids, cutter_ids, delete_input=True):
    """Subtract cutter Breps from base Breps and return IDs for the results."""
    base_ids = list(base_ids)
    cutter_ids = list(cutter_ids)
    if not base_ids or not cutter_ids:
        raise ValueError("boolean_difference requires base and cutter object IDs.")

    base_breps = _breps_from_ids(base_ids)
    cutter_breps = _breps_from_ids(cutter_ids)
    tolerance = sc.doc.ModelAbsoluteTolerance
    results = Rhino.Geometry.Brep.CreateBooleanDifference(
        base_breps, cutter_breps, tolerance
    )
    return _add_boolean_results(
        results, base_ids[0], base_ids + cutter_ids, delete_input
    )


def rectangular_array(
    object_ids, x_count, y_count, x_spacing, y_spacing, include_original=True
):
    """Create an XY rectangular array. Counts include the original object."""
    if x_count < 1 or y_count < 1:
        raise ValueError("Array counts must be at least 1.")
    if _is_object_list(object_ids):
        result_ids = []
        for object_id in object_ids:
            result_ids.extend(
                rectangular_array(
                    object_id,
                    x_count,
                    y_count,
                    x_spacing,
                    y_spacing,
                    include_original,
                )
            )
        return result_ids

    object_id = object_ids
    result_ids = [object_id] if include_original else []
    for x_index in range(x_count):
        for y_index in range(y_count):
            if include_original and x_index == 0 and y_index == 0:
                continue
            transform = Rhino.Geometry.Transform.Translation(
                x_index * x_spacing,
                y_index * y_spacing,
                0.0,
            )
            result_ids.append(_transform_object(object_id, transform, copy=True))
    return result_ids


def circular_array(
    object_ids, center, count, angle_degrees=360.0, include_original=True
):
    """Create a Z-axis circular array. Count includes the original object."""
    if count < 1:
        raise ValueError("Array count must be at least 1.")
    if _is_object_list(object_ids):
        result_ids = []
        for object_id in object_ids:
            result_ids.extend(
                circular_array(
                    object_id, center, count, angle_degrees, include_original
                )
            )
        return result_ids

    object_id = object_ids
    result_ids = [object_id] if include_original else []
    step = angle_degrees / count
    for index in range(count):
        if include_original and index == 0:
            continue
        transform = Rhino.Geometry.Transform.Rotation(
            math.radians(index * step),
            Rhino.Geometry.Vector3d.ZAxis,
            _point3d(center),
        )
        result_ids.append(_transform_object(object_id, transform, copy=True))
    return result_ids


def mirror(
    object_ids, plane_origin=(0.0, 0.0, 0.0), plane_normal=(1.0, 0.0, 0.0), copy=True
):
    """Mirror one object ID or a list of IDs across a plane."""
    plane = Rhino.Geometry.Plane(
        _point3d(plane_origin), Rhino.Geometry.Vector3d(*plane_normal)
    )
    transform = Rhino.Geometry.Transform.Mirror(plane)
    return _map_objects(
        object_ids, lambda object_id: _transform_object(object_id, transform, copy)
    )


def move(object_ids, vector, copy=False):
    """Move one object ID or a list of IDs by an XYZ vector."""
    transform = Rhino.Geometry.Transform.Translation(Rhino.Geometry.Vector3d(*vector))
    return _map_objects(
        object_ids, lambda object_id: _transform_object(object_id, transform, copy)
    )


def rotate_2d(object_ids, angle_degrees, center=(0.0, 0.0, 0.0), copy=False):
    """Rotate one object ID or a list of IDs around the world Z axis."""
    transform = Rhino.Geometry.Transform.Rotation(
        math.radians(angle_degrees),
        Rhino.Geometry.Vector3d.ZAxis,
        _point3d(center),
    )
    return _map_objects(
        object_ids, lambda object_id: _transform_object(object_id, transform, copy)
    )


def rotate_3d(object_ids, angle_degrees, axis_start, axis_end, copy=False):
    """Rotate one object ID or a list of IDs around an arbitrary axis."""
    start = _point3d(axis_start)
    axis = _point3d(axis_end) - start
    if axis.IsZero:
        raise ValueError("Rotation axis start and end must be different.")
    transform = Rhino.Geometry.Transform.Rotation(
        math.radians(angle_degrees), axis, start
    )
    return _map_objects(
        object_ids, lambda object_id: _transform_object(object_id, transform, copy)
    )


def create_polygon(center, radius, sides, z=0.0):
    """Create a closed regular polygon on the world XY plane."""
    if sides < 3:
        raise ValueError("A polygon needs at least three sides.")

    center_x, center_y = center[0], center[1]
    points = []
    for index in range(sides):
        angle = 2.0 * math.pi * index / sides
        points.append(
            Rhino.Geometry.Point3d(
                center_x + radius * math.cos(angle),
                center_y + radius * math.sin(angle),
                z,
            )
        )
    points.append(points[0])
    return sc.doc.Objects.AddPolyline(points)


def _polygon_to_single_face(polygon_id):
    """Create a planar Brep face from a closed polygon curve."""
    curve = _find_object(polygon_id).Geometry
    if not isinstance(curve, Rhino.Geometry.Curve) or not curve.IsClosed:
        raise ValueError("polygon_to_face requires a closed curve object ID.")

    breps = Rhino.Geometry.Brep.CreatePlanarBreps(curve, sc.doc.ModelAbsoluteTolerance)
    if not breps:
        return None
    attributes = _find_object(polygon_id).Attributes.Duplicate()
    return sc.doc.Objects.AddBrep(breps[0], attributes)


def polygon_to_face(polygon_ids):
    """Create faces from one closed polygon ID or a list of polygon IDs."""
    return _map_objects(polygon_ids, _polygon_to_single_face)


def _single_face_to_solid(face_id, height, direction):
    """Extrude a planar Brep face into a capped solid."""
    brep = _find_object(face_id).Geometry
    if not isinstance(brep, Rhino.Geometry.Brep) or brep.Faces.Count != 1:
        raise ValueError("face_to_solid requires a single-face Brep object ID.")

    vector = Rhino.Geometry.Vector3d(*direction)
    if not vector.Unitize():
        raise ValueError("Extrusion direction cannot be zero.")
    solid = brep.Faces[0].CreateExtrusion(vector * height, True)
    if not solid:
        return None
    attributes = _find_object(face_id).Attributes.Duplicate()
    return sc.doc.Objects.AddBrep(solid, attributes)


def face_to_solid(face_ids, height, direction=(0.0, 0.0, 1.0)):
    """Extrude one Brep face ID or a list of face IDs into capped solids."""
    return _map_objects(
        face_ids,
        lambda face_id: _single_face_to_solid(face_id, height, direction),
    )


def _solid_from_single_path(path_id, section, width=None, height=None, radius=None):
    """Sweep a rectangular or circular section along an open or closed curve.

    section must be "rectangle" or "circle". The path is kept in the document.
    """
    curve = _find_object(path_id).Geometry
    tolerance = sc.doc.ModelAbsoluteTolerance
    if not isinstance(curve, Rhino.Geometry.Curve) or curve.GetLength() <= tolerance:
        raise ValueError("solid_from_path requires a non-zero-length curve object ID.")

    if section == "rectangle":
        if width is None or height is None or width <= 0.0 or height <= 0.0:
            raise ValueError("Rectangle section requires positive width and height.")

        tangent = curve.TangentAtStart
        if not tangent.Unitize():
            raise ValueError("Path curve has no valid tangent at its start.")
        profile_plane = Rhino.Geometry.Plane(curve.PointAtStart, tangent)
        profile = Rhino.Geometry.Rectangle3d(
            profile_plane,
            Rhino.Geometry.Interval(-width / 2.0, width / 2.0),
            Rhino.Geometry.Interval(-height / 2.0, height / 2.0),
        ).ToNurbsCurve()
        # Segmented sweep handles polyline kinks such as a hexagon's corners.
        solids = Rhino.Geometry.Brep.CreateFromSweepSegmented(
            curve, profile, curve.IsClosed, tolerance
        )
        if not curve.IsClosed:
            solids = [solid.CapPlanarHoles(tolerance) for solid in solids]
        if not solids or any(solid is None for solid in solids):
            raise RuntimeError(
                "Rhino could not create a capped rectangular path solid."
            )
    elif section == "circle":
        if radius is None or radius <= 0.0:
            raise ValueError("Circle section requires a positive radius.")
        cap_mode = (
            getattr(Rhino.Geometry.PipeCapMode, "None")
            if curve.IsClosed
            else Rhino.Geometry.PipeCapMode.Flat
        )
        solids = Rhino.Geometry.Brep.CreatePipe(
            curve,
            radius,
            False,
            cap_mode,
            False,
            tolerance,
            sc.doc.ModelAngleToleranceRadians,
        )
        if not solids:
            raise RuntimeError("Rhino could not create a circular path solid.")
    else:
        raise ValueError('section must be "rectangle" or "circle".')

    attributes = _find_object(path_id).Attributes.Duplicate()
    result_ids = [sc.doc.Objects.AddBrep(solid, attributes) for solid in solids]
    return result_ids[0] if len(result_ids) == 1 else result_ids


def solid_from_path(path_ids, section, width=None, height=None, radius=None):
    """Sweep a section along one path ID or a list of path IDs.

    A single path returns one object ID (or a list when Rhino creates multiple
    Breps). A list of paths always returns a flat list of generated object IDs.
    """
    if not isinstance(path_ids, (list, tuple)):
        return _solid_from_single_path(path_ids, section, width, height, radius)

    result_ids = []
    for path_id in path_ids:
        result = _solid_from_single_path(path_id, section, width, height, radius)
        if isinstance(result, list):
            result_ids.extend(result)
        else:
            result_ids.append(result)
    return result_ids


def solid_from_line_path(path_id, section, width=None, height=None, radius=None):
    """Backward-compatible name for solid_from_path()."""
    return solid_from_path(path_id, section, width, height, radius)


def _fillet_single_object(object_id, radius, edge_indices, delete_input):
    """Round selected Brep edges, or all edges when edge_indices is omitted."""
    brep = _find_object(object_id).Geometry
    if not isinstance(brep, Rhino.Geometry.Brep):
        raise ValueError("fillet_edges requires a Brep object ID.")
    if radius <= 0.0:
        raise ValueError("Fillet radius must be positive.")

    if edge_indices is None:
        edge_indices = list(range(brep.Edges.Count))
    else:
        edge_indices = list(edge_indices)
    if not edge_indices:
        raise ValueError("Select at least one Brep edge to fillet.")
    if min(edge_indices) < 0 or max(edge_indices) >= brep.Edges.Count:
        raise ValueError("An edge index is outside the Brep edge range.")

    radii = [radius] * len(edge_indices)
    results = Rhino.Geometry.Brep.CreateFilletEdges(
        brep,
        edge_indices,
        radii,
        radii,
        Rhino.Geometry.BlendType.Fillet,
        Rhino.Geometry.RailType.RollingBall,
        sc.doc.ModelAbsoluteTolerance,
    )
    return _add_boolean_results(results, object_id, [object_id], delete_input)


def fillet_edges(object_ids, radius, edge_indices=None, delete_input=True):
    """Round edges on one Brep ID or each Brep ID in a list."""
    if not _is_object_list(object_ids):
        return _fillet_single_object(object_ids, radius, edge_indices, delete_input)

    result_ids = []
    for object_id in object_ids:
        result_ids.extend(
            _fillet_single_object(object_id, radius, edge_indices, delete_input)
        )
    return result_ids


def _trim_single_curve(curve_id, start, end, delete_input):
    curve = _find_object(curve_id).Geometry
    if not isinstance(curve, Rhino.Geometry.Curve):
        raise ValueError("trim_curve requires a curve object ID.")
    if not 0.0 <= start < end <= 1.0:
        raise ValueError("Curve trim start and end must satisfy 0 <= start < end <= 1.")

    domain = curve.Domain
    interval = Rhino.Geometry.Interval(
        domain.T0 + start * (domain.T1 - domain.T0),
        domain.T0 + end * (domain.T1 - domain.T0),
    )
    trimmed_curve = curve.Trim(interval)
    if not trimmed_curve:
        raise RuntimeError("Rhino could not trim the curve.")

    attributes = _find_object(curve_id).Attributes.Duplicate()
    result_id = sc.doc.Objects.AddCurve(trimmed_curve, attributes)
    if delete_input:
        sc.doc.Objects.Delete(curve_id, True)
    return result_id


def trim_curve(curve_ids, start, end, delete_input=True):
    """Keep the normalized interval [start, end] of one or more curves."""
    return _map_objects(
        curve_ids,
        lambda curve_id: _trim_single_curve(curve_id, start, end, delete_input),
    )


def _trim_single_brep(brep_id, cutter_id, delete_input, keep_inside):
    brep = _find_object(brep_id).Geometry
    cutter = _find_object(cutter_id).Geometry
    if not isinstance(brep, Rhino.Geometry.Brep):
        raise ValueError("trim_brep requires Brep object IDs to trim.")
    if not isinstance(cutter, Rhino.Geometry.Brep):
        raise ValueError("trim_brep requires a Brep cutter ID.")

    cutter_to_use = cutter.DuplicateBrep()
    if not keep_inside:
        cutter_to_use.Flip()
    results = brep.Trim(cutter_to_use, sc.doc.ModelAbsoluteTolerance)
    return _add_boolean_results(results, brep_id, [brep_id], delete_input)


def trim_brep(brep_ids, cutter_id, delete_input=True, keep_inside=True):
    """Trim one or more Breps with an oriented Brep cutter.

    keep_inside=True retains the inside of a closed cutter, or the side opposite
    an open cutter's normal. The cutter is preserved.
    """
    if not _is_object_list(brep_ids):
        return _trim_single_brep(brep_ids, cutter_id, delete_input, keep_inside)

    result_ids = []
    for brep_id in brep_ids:
        result_ids.extend(
            _trim_single_brep(brep_id, cutter_id, delete_input, keep_inside)
        )
    return result_ids


def _trim_single_brep_by_plane(brep_id, plane, delete_input):
    brep = _find_object(brep_id).Geometry
    if not isinstance(brep, Rhino.Geometry.Brep):
        raise ValueError("trim_brep_by_plane requires Brep object IDs to trim.")

    results = brep.Trim(plane, sc.doc.ModelAbsoluteTolerance)
    return _add_boolean_results(results, brep_id, [brep_id], delete_input)


def trim_brep_by_plane(
    brep_ids,
    cutter_origin,
    cutter_normal,
    keep_negative_side=True,
    delete_input=True,
):
    """Trim Breps with an infinite cutter plane and retain one side.

    keep_negative_side=True retains the side opposite cutter_normal. Set it to
    False to retain the cutter_normal direction instead.
    """
    normal = Rhino.Geometry.Vector3d(*cutter_normal)
    if not normal.Unitize():
        raise ValueError("Cutter plane normal cannot be zero.")
    if not keep_negative_side:
        normal = -normal
    plane = Rhino.Geometry.Plane(_point3d(cutter_origin), normal)

    if not _is_object_list(brep_ids):
        return _trim_single_brep_by_plane(brep_ids, plane, delete_input)

    result_ids = []
    for brep_id in brep_ids:
        result_ids.extend(_trim_single_brep_by_plane(brep_id, plane, delete_input))
    return result_ids
