import math

# %% Design variables
PANEL_SIZE = 500.0
FRAME_WIDTH = 6.0
width = 2.0  # Width of every mesh bar.
HEIGHT = 2.0

HUB_RADIUS = 10.0
HUB_CLEARANCE = 12.0
RADIAL_BAND_COUNT = 12
DIAGONAL_SPACING = 20.0


def _point_on_ray(angle, distance):
    """Return an XY point at distance along an angle in degrees."""
    radians = math.radians(angle)
    return (distance * math.cos(radians), distance * math.sin(radians), 0.0)


def _lerp(start, end, amount):
    """Return a point between start and end."""
    return tuple(
        start[index] + (end[index] - start[index]) * amount
        for index in range(3)
    )


def _square_boundary_point(angle, half_size):
    """Return where a ray from the origin intersects the square boundary."""
    radians = math.radians(angle)
    x_direction = math.cos(radians)
    y_direction = math.sin(radians)
    distance = half_size / max(abs(x_direction), abs(y_direction))
    return (distance * x_direction, distance * y_direction, 0.0)


def _diagonal_segment(offset, half_size):
    """Return a segment of x + y = offset clipped to the square panel."""
    if offset <= 0.0:
        return (-half_size, offset + half_size, 0.0), (offset + half_size, -half_size, 0.0)
    return (offset - half_size, half_size, 0.0), (half_size, offset - half_size, 0.0)


def _add_bar(tools, start, end, layer_name):
    """Create one rectangular mesh bar and remove its temporary line path."""
    path_id = tools.create_line(start, end)
    tools.add_to_layer(path_id, layer_name)
    bar_id = tools.solid_from_path(path_id, "rectangle", width=width, height=HEIGHT)
    tools.delete_object(path_id)
    return tools.add_to_layer(bar_id, layer_name)


def _add_radial_weave(tools, half_size, layer_name):
    """Create eight fan-shaped woven regions around the hub."""
    hub_distance = HUB_RADIUS + HUB_CLEARANCE
    for sector in range(8):
        start_angle = sector * 45.0
        end_angle = (sector + 1) * 45.0
        inner_start = _point_on_ray(start_angle, hub_distance)
        inner_end = _point_on_ray(end_angle, hub_distance)
        outer_start = _square_boundary_point(start_angle, half_size)
        outer_end = _square_boundary_point(end_angle, half_size)

        # Radial edges organize the eight sectors.
        _add_bar(tools, inner_start, outer_start, layer_name)

        # Each band spans the two rays, creating the woven fan pattern.
        for index in range(1, RADIAL_BAND_COUNT + 1):
            amount = index / float(RADIAL_BAND_COUNT + 1)
            _add_bar(
                tools,
                _lerp(inner_start, outer_start, amount),
                _lerp(inner_end, outer_end, amount),
                layer_name,
            )


def _add_diagonal_weave(tools, half_size, layer_name):
    """Add the continuous diagonal strand family visible across the panel."""
    count = int((2.0 * half_size) / DIAGONAL_SPACING)
    for index in range(-count, count + 1):
        offset = index * DIAGONAL_SPACING
        if -2.0 * half_size < offset < 2.0 * half_size:
            start, end = _diagonal_segment(offset, half_size)
            _add_bar(tools, start, end, layer_name)


# %% Rhino build
def build_model():
    """Build a square radial woven-mesh panel based on the reference image."""
    import tools

    if PANEL_SIZE <= 0.0 or FRAME_WIDTH <= 0.0:
        raise ValueError("PANEL_SIZE and FRAME_WIDTH must be positive.")
    if width <= 0.0 or HEIGHT <= 0.0 or DIAGONAL_SPACING <= 0.0:
        raise ValueError("width, HEIGHT, and DIAGONAL_SPACING must be positive.")
    if RADIAL_BAND_COUNT < 1 or HUB_RADIUS <= 0.0 or HUB_CLEARANCE < 0.0:
        raise ValueError("Hub settings and RADIAL_BAND_COUNT are invalid.")

    half_size = PANEL_SIZE / 2.0
    if HUB_RADIUS + HUB_CLEARANCE >= half_size:
        raise ValueError("Hub settings leave no space for the radial mesh.")

    layer_name = tools.begin_model()

    # Square outer frame.
    frame_path = tools.create_rectangle((-half_size, -half_size, 0.0), PANEL_SIZE, PANEL_SIZE)
    tools.add_to_layer(frame_path, layer_name)
    frame_id = tools.solid_from_path(
        frame_path, "rectangle", width=FRAME_WIDTH, height=HEIGHT
    )
    tools.delete_object(frame_path)
    tools.add_to_layer(frame_id, layer_name)

    # Circular center node.
    hub_path = tools.create_circle((0.0, 0.0, 0.0), HUB_RADIUS)
    tools.add_to_layer(hub_path, layer_name)
    hub_id = tools.solid_from_path(hub_path, "rectangle", width=width, height=HEIGHT)
    tools.delete_object(hub_path)
    tools.add_to_layer(hub_id, layer_name)

    _add_radial_weave(tools, half_size, layer_name)
    _add_diagonal_weave(tools, half_size, layer_name)
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
