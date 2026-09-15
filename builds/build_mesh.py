import math

# %% Parameters
SMALL_HEX_SIDE = 2.0
HEXES_PER_BIG_HEX_SIDE = 5


def _hex_center(q, r, side):
    """Return the center of a flat-top hexagon in axial grid coordinates."""
    return (
        1.5 * side * q,
        math.sqrt(3.0) * side * (r + 0.5 * q),
        0.0,
    )


def _hexagon_cells(per_side):
    """Yield axial coordinates for a hexagonal cluster of small hexagons."""
    radius = per_side - 1
    for q in range(-radius, radius + 1):
        for r in range(-radius, radius + 1):
            if max(abs(q), abs(r), abs(-q - r)) <= radius:
                yield q, r


# The build loop only reads this list. Replace it with hand-picked centers to
# create any custom combination of small hexagons.
HEXAGON_CENTERS = [
    _hex_center(q, r, SMALL_HEX_SIDE) for q, r in _hexagon_cells(HEXES_PER_BIG_HEX_SIDE)
]


# %% Rhino build
def build_model():
    """Create one polygon object for every defined small-hexagon center."""
    import tools

    if SMALL_HEX_SIDE <= 0.0:
        raise ValueError("SMALL_HEX_SIDE must be positive.")
    if not HEXAGON_CENTERS:
        raise ValueError("Define at least one center in HEXAGON_CENTERS.")

    layer_name = tools.begin_model()
    for center in HEXAGON_CENTERS:
        hexagon = tools.add_to_layer(
            tools.create_polygon(center=center, sides=6, radius=SMALL_HEX_SIDE),
            layer_name,
        )
        tools.solid_from_path(hexagon, "rectangle", width=0.2, height=0.5)
        tools.delete_object(hexagon)

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
