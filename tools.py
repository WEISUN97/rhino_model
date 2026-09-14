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
    plane = Rhino.Geometry.Plane(Rhino.Geometry.Point3d(*origin), Rhino.Geometry.Vector3d.ZAxis)
    rectangle = Rhino.Geometry.Rectangle3d(plane, width, height)
    return sc.doc.Objects.AddPolyline(rectangle.ToPolyline())


def create_circle(center, radius):
    circle = Rhino.Geometry.Circle(Rhino.Geometry.Point3d(*center), radius)
    return sc.doc.Objects.AddCircle(circle)


def create_box(length, width, height, origin=(0.0, 0.0, 0.0)):
    plane = Rhino.Geometry.Plane(Rhino.Geometry.Point3d(*origin), Rhino.Geometry.Vector3d.ZAxis)
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
    plane = Rhino.Geometry.Plane(Rhino.Geometry.Point3d(*center), Rhino.Geometry.Vector3d.ZAxis)
    cylinder = Rhino.Geometry.Cylinder(Rhino.Geometry.Circle(plane, radius), height)
    return sc.doc.Objects.AddBrep(cylinder.ToBrep(True, True))
