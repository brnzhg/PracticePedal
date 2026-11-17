"""Show the model in OCP CAD Viewer (VS Code extension, or standalone in a browser).

    uv run python -m pedal_cad.view                 # assembly at rest
    uv run python -m pedal_cad.view exploded        # parts spread out vertically
    uv run python -m pedal_cad.view pressed left    # one key (left/center/right) at its stop
    uv run python -m pedal_cad.view top sled        # just the named parts

Needs the OCP CAD Viewer panel open in VS Code (it listens on port 3939).
The camera is kept between runs, so edit params.py, re-run, and compare.
If nothing appears on the first run, press the viewer's resize/iso buttons.
"""

import sys

from build123d import Pos
from ocp_vscode import Camera, set_defaults, show

from . import parts as pt
from .build import build
from .params import P

COLORS = {"tray": "DimGray", "sled": "Orange", "top": "SteelBlue", "riser": "Tomato"}
LIFT = {"sled": 30, "top": 70, "riser": 95}  # exploded offsets, as in exploded.svg


def scene(args):
    printed, bought = build()
    objs = {**printed, **bought}
    mode = args[0] if args else "assembly"

    if mode == "exploded":
        objs = {
            n: Pos(0, 0, LIFT.get(n, 48 if n.startswith("choc") else 30 if n in bought else 0)) * s
            for n, s in objs.items()
            if n != "stop_pad"
        }
    elif mode == "pressed":
        key = args[1] if len(args) > 1 else "left"
        region = pt.key_region(P, key)
        top = objs["top"]
        objs["top"] = top - region
        moving = top & region
        if key == "center":
            moving = moving + objs.pop("riser")
        objs[f"{key}_key"] = pt.press(moving, P, key)
        x = P.switch_xs[["left", "center", "right"].index(key)]
        objs[f"choc_{key}"] = pt.make_choc(P, x, pressed=P.stop_travel)
    elif mode != "assembly":
        missing = [a for a in args if a not in objs]
        if missing:
            sys.exit(f"unknown part(s) {missing}; choose from {list(objs)}")
        objs = {n: objs[n] for n in args}

    return {n: s for n, s in objs.items() if s.volume > 0}


def main():
    objs = scene(sys.argv[1:])
    set_defaults(reset_camera=Camera.KEEP)
    show(
        *objs.values(),
        names=list(objs),
        colors=[COLORS["top"] if n.endswith("_key") else COLORS.get(n, "LightGray") for n in objs],
    )


if __name__ == "__main__":
    main()
