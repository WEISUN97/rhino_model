import math

import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc

LAYER_NAME = "GeneratedGeometry"


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


def add_to_layer(object_id, layer_name=LAYER_NAME):
    if object_id:
        rs.ObjectLayer(object_id, layer_name)
    return object_id


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
    object_id, x_count, y_count, x_spacing, y_spacing, include_original=True
):
    """Create an XY rectangular array. Counts include the original object."""
    if x_count < 1 or y_count < 1:
        raise ValueError("Array counts must be at least 1.")

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
    object_id, center, count, angle_degrees=360.0, include_original=True
):
    """Create a Z-axis circular array. Count includes the original object."""
    if count < 1:
        raise ValueError("Array count must be at least 1.")

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
    object_id, plane_origin=(0.0, 0.0, 0.0), plane_normal=(1.0, 0.0, 0.0), copy=True
):
    """Mirror an object across a plane defined by an origin and normal."""
    plane = Rhino.Geometry.Plane(
        _point3d(plane_origin), Rhino.Geometry.Vector3d(*plane_normal)
    )
    return _transform_object(object_id, Rhino.Geometry.Transform.Mirror(plane), copy)


def move(object_id, vector, copy=False):
    """Move an object by an XYZ vector."""
    transform = Rhino.Geometry.Transform.Translation(Rhino.Geometry.Vector3d(*vector))
    return _transform_object(object_id, transform, copy)


def rotate_2d(object_id, angle_degrees, center=(0.0, 0.0, 0.0), copy=False):
    """Rotate an object around the world Z axis."""
    transform = Rhino.Geometry.Transform.Rotation(
        math.radians(angle_degrees),
        Rhino.Geometry.Vector3d.ZAxis,
        _point3d(center),
    )
    return _transform_object(object_id, transform, copy)


def rotate_3d(object_id, angle_degrees, axis_start, axis_end, copy=False):
    """Rotate an object around the axis from axis_start to axis_end."""
    start = _point3d(axis_start)
    axis = _point3d(axis_end) - start
    if axis.IsZero:
        raise ValueError("Rotation axis start and end must be different.")
    transform = Rhino.Geometry.Transform.Rotation(
        math.radians(angle_degrees), axis, start
    )
    return _transform_object(object_id, transform, copy)


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


def polygon_to_face(polygon_id):
    """Create a planar Brep face from a closed polygon curve."""
    curve = _find_object(polygon_id).Geometry
    if not isinstance(curve, Rhino.Geometry.Curve) or not curve.IsClosed:
        raise ValueError("polygon_to_face requires a closed curve object ID.")

    breps = Rhino.Geometry.Brep.CreatePlanarBreps(curve, sc.doc.ModelAbsoluteTolerance)
    if not breps:
        return None
    attributes = _find_object(polygon_id).Attributes.Duplicate()
    return sc.doc.Objects.AddBrep(breps[0], attributes)


def face_to_solid(face_id, height, direction=(0.0, 0.0, 1.0)):
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
