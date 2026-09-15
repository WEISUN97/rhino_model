# RunPythonScript


def build_model():
    """Build the current demo model. Keep its parameters close to the model."""
    # Import only inside Rhino; normal VS Code Python has no Rhino API.
    import tools

    box_l = 20.0
    box_w = 10.0
    box_h = 5.0
    sphere_radius = 3.0
    cylinder_radius = 5.0
    cylinder_height = 8.0

    layer_name = tools.begin_model()

    tools.add_to_layer(tools.create_point(0.0, -8.0, 0.0), layer_name)
    line = tools.add_to_layer(
        tools.create_line((0.0, -5.0, 0.0), (12.0, -5.0, 0.0)), layer_name
    )
    # surface
    tools.add_to_layer(tools.create_rectangle((0.0, -2.0, 0.0), 12.0, 6.0), layer_name)
    tools.add_to_layer(tools.create_circle((6.0, 10.0, 0.0), 4.0), layer_name)

    # 3D objects
    box1 = tools.add_to_layer(
        tools.create_box(box_l, box_w, box_h, origin=(0.0, 0.0, 0.0)), layer_name
    )
    box2 = tools.add_to_layer(
        tools.create_box(5, 20, 10, origin=(10.0, -5.0, -5.0)), layer_name
    )
    sphere = tools.add_to_layer(
        tools.create_sphere(sphere_radius, center=(0, 5.0, sphere_radius)),
        layer_name,
    )
    tools.add_to_layer(
        tools.create_cylinder(
            cylinder_radius, cylinder_height, center=(60.0, 5.0, 0.0)
        ),
        layer_name,
    )
    hexagon = tools.add_to_layer(
        tools.create_polygon(center=(0.0, 0.0, 0.0), sides=6, radius=4.0), layer_name
    )

    # Operations
    # boolean operations
    # tools.boolean_difference([box], [sphere], delete_input=True)

    # Mirror two point determines the normal direction of the mirror plane.
    # tools.mirror(box, (0.0, 0.0, 0.0), (0.0, 1.0, 0.0), copy=True)

    # path
    path = tools.solid_from_path(hexagon, "rectangle", width=1.0, height=2.0)
    tools.trim_brep([box1], box2, delete_input=True, keep_inside=True)
    ###
    tools.finish_model()


# %% Run in Rhino
if __name__ == "__main__":
    # Running this file from VS Code sends launcher.py to Rhino.
    from pathlib import Path
    import sys

    project_dir = str(Path(__file__).resolve().parent.parent)
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)

    from run_rhino import run_in_rhino

    run_in_rhino("builds." + Path(__file__).stem)
