import tools

# RunPythonScript


def build_model():
    """Build the current demo model. Keep its parameters close to the model."""
    box_l = 20.0
    box_w = 10.0
    box_h = 5.0
    sphere_radius = 3.0
    cylinder_radius = 5.0
    cylinder_height = 8.0

    layer_name = tools.begin_model()

    tools.add_to_layer(tools.create_point(0.0, -8.0, 0.0), layer_name)
    tools.add_to_layer(
        tools.create_line((0.0, -5.0, 0.0), (12.0, -5.0, 0.0)), layer_name
    )
    tools.add_to_layer(tools.create_rectangle((0.0, -2.0, 0.0), 12.0, 6.0), layer_name)
    tools.add_to_layer(tools.create_circle((6.0, 10.0, 0.0), 4.0), layer_name)

    tools.add_to_layer(tools.create_box(box_l, box_w, box_h), layer_name)
    tools.add_to_layer(
        tools.create_sphere(sphere_radius, center=(35.0, 5.0, sphere_radius)),
        layer_name,
    )
    tools.add_to_layer(
        tools.create_cylinder(
            cylinder_radius, cylinder_height, center=(60.0, 5.0, 0.0)
        ),
        layer_name,
    )

    tools.finish_model()
