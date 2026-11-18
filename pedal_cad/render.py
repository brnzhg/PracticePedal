"""Shaded PNG renders of the model for the README (needs the dev dependencies).

    uv run python -m pedal_cad.render

Writes out/renders/*.png. Slower than the SVG drawings and not part of the CI build;
re-run it and commit the PNGs when the geometry changes noticeably.
"""

from pathlib import Path

import numpy as np
import pyvista as pv
from build123d import Pos

from . import parts as pt
from .build import build
from .params import P

pv.OFF_SCREEN = True
pv.global_theme.allow_empty_mesh = True
SIZE = (1600, 1000)

COLORS = {
    "tray": "#4a4f57",
    "sled": "#e8973a",
    "top": "#3f7fbf",
    "riser": "#d9534f",
    "nano": "#2b2b4a",
    "battery": "#9fc6e8",
    "power_switch": "#c9c9c9",
    "stop_pad": "#7a6a55",
    "choc": "#f2f2f2",
}


def color(name):
    return COLORS["choc" if name.startswith("choc") else name if name in COLORS else "top"]


def mesh(shape):
    verts, tris = shape.tessellate(0.05, 0.2)
    pts = np.array([(v.X, v.Y, v.Z) for v in verts])
    faces = np.hstack([np.full((len(tris), 1), 3), np.array(tris)]).ravel()
    return pv.PolyData(pts, faces).compute_normals(split_vertices=True, feature_angle=35)


def plotter():
    p = pv.Plotter(off_screen=True, window_size=SIZE, lighting="light kit")
    p.set_background("white")
    p.enable_anti_aliasing("ssaa")
    return p


def add(p, name, shape, opacity=1.0):
    m = mesh(shape)
    p.add_mesh(m, color=color(name), smooth_shading=True, ambient=0.25, diffuse=0.85,
               specular=0.15, opacity=opacity)
    p.add_mesh(m.extract_feature_edges(35, boundary_edges=False, manifold_edges=False),
               color="#1a1a1a", line_width=1.2, opacity=0.6 * opacity)


def shoot(p, path, position, focal, up=(0, 0, 1), zoom=1.0):
    p.camera_position = [position, focal, up]
    p.camera.zoom(zoom)
    p.screenshot(str(path))
    p.close()
    print("wrote", path)


def hero(printed, bought, out):
    p = plotter()
    for n, s in {**printed, **bought}.items():
        add(p, n, s)
    shoot(p, out / "assembly.png", (-150, -260, 230), (0, 0, 5), zoom=1.25)


def exploded(printed, bought, out):
    lift = {"sled": 30, "top": 70, "riser": 95}
    p = plotter()
    for n, s in {**printed, **bought}.items():
        if n == "stop_pad":
            continue
        dz = lift.get(n, 48 if n.startswith("choc") else 30 if n in bought else 0)
        add(p, n, Pos(0, 0, dz) * s)
    p.window_size = (1600, 1300)
    shoot(p, out / "exploded.png", (-200, -330, 300), (0, 0, 45), zoom=1.3)


def cutaway(printed, bought, out, pressed=False):
    p = plotter()
    shapes = {**printed, **bought}
    if pressed:
        shapes["top"] = printed["top"] - pt.key_region(P, "right")
        shapes["top_key"] = pt.press(printed["top"] & pt.key_region(P, "right"), P, "right")
        shapes["choc_right"] = pt.make_choc(P, P.pedal_xc, pressed=P.stop_travel)
    x = P.pedal_xc
    slab = pt.box(x - 25, x, -200, 200, -50, 100)       # a 25 mm slice, cut face towards the camera
    for n, s in shapes.items():
        c = s & slab
        if c.volume > 0:
            add(p, n, c)
    for (y, z), t in (((P.switch_y, 6), "Choc switch"), ((P.hinge_y, 17), "living hinge"),
                      ((-49, 12.2), "stop pad"), ((5, 4), "sled"), ((20, 0.5), "tray"),
                      ((-20, 18.6), "pedal")):
        p.add_point_labels(np.array([(x + 0.5, y, z)]), [t], font_size=22, text_color="white",
                           shape_color="#333333", shape_opacity=0.85, point_size=8, point_color="#333333",
                           render_points_as_spheres=True, always_visible=True, margin=4)
    name = "section_pedal_pressed.png" if pressed else "section_pedal.png"
    p.window_size = (1600, 560)
    shoot(p, out / name, (x + 400, -70, 70), (x, 0, 9), zoom=3.4)


def wiring(printed, bought, out):
    """Sled from below with the wires drawn in as tubes."""
    p = plotter()
    for n in ("sled", "nano", "battery", "power_switch", "choc_left", "choc_center", "choc_right"):
        add(p, n, {**printed, **bought}[n])

    z = 2.0                                     # wire level, just below the sled
    pin_y = [P.nano_y1 - 2.53 - 2.54 * i for i in range(12)]
    px_l, px_r = 7.62, -7.62                    # pin rows (see draw.wiring_diagram)

    def wire(pts2d, col, ends=()):
        pts = [(x, y, z) for x, y in pts2d]
        pts = [(*pts2d[0], 4.0)] + pts + [(*pts2d[-1], 4.8)]
        line = pv.lines_from_points(np.array(pts, float))
        p.add_mesh(line.tube(radius=0.55, n_sides=12), color=col, smooth_shading=True)

    def label(xy, text, col):
        p.add_point_labels(np.array([(*xy, 0.0)]), [text], font_size=26, text_color="white",
                           shape_color=col, shape_opacity=0.95, show_points=False,
                           always_visible=True, margin=5, bold=True)

    cols = {"left": "#2a9d4b", "center": "#1f6fd1", "right": "#9b3fc4"}
    pin = {"left": 4, "center": 5, "right": 6}          # D2, D3, D4 in the left row
    y_sig, y_gnd = -19.0, -22.5
    for i, (name, x) in enumerate(zip(("left", "center", "right"), P.switch_xs)):
        a = (x, P.switch_y + 5.9)
        ys = y_sig + 0.8 * i
        xv = px_l + 4.5 + 1.5 * i
        wire([a, (a[0], ys), (xv, ys), (xv, pin_y[pin[name]]), (px_l, pin_y[pin[name]])], cols[name])
        label((x, P.switch_y - 12), {"left": "LEFT pedal", "center": "CENTRE", "right": "RIGHT pedal"}[name]
              + f" to D{pin[name] - 2}", cols[name])
    gs = [(x + 5.0, P.switch_y + 3.8) for x in P.switch_xs]
    for g in gs:
        wire([g, (g[0], y_gnd)], "#222222")
    xg = px_l + 10.5
    wire([gs[0], (gs[0][0], y_gnd), (gs[2][0], y_gnd), (gs[2][0], y_gnd)], "#222222")
    wire([(xg, y_gnd), (xg, y_gnd), (xg, pin_y[3]), (px_l, pin_y[3])], "#222222")
    label((xg + 4, -8), "other pins to GND", "#222222")

    ps = bought["power_switch"].bounding_box()
    lead_y = 28.5
    bplus, bminus = (P.batt_x1, lead_y + 1.2), (P.batt_x1, lead_y - 1.2)
    sw_c, sw_o = (P.psw_x, ps.min.Y), (P.psw_x + 2.5, ps.min.Y)
    wire([bplus, (bplus[0] + 2, bplus[1]), (bplus[0] + 2, sw_c[1] - 2), (sw_c[0], sw_c[1] - 2), sw_c], "#d62828")
    wire([sw_o, (sw_o[0], sw_o[1] - 4.5), (px_r - 3.5, sw_o[1] - 4.5), (px_r - 3.5, pin_y[0]), (px_r, pin_y[0])],
         "#e76f51")
    wire([bminus, (px_r - 1.8, bminus[1]), (px_r - 1.8, pin_y[1]), (px_r, pin_y[1])], "#222222")
    label((-45, 20), "battery + to switch to B+", "#d62828")
    label((-45, 12), "battery - to B-", "#222222")
    label((0, 56), "rear edge (USB)", "#555555")
    label((0, 30), "nice!nano", "#2b2b4a")
    p.add_text("Sled seen from below, as you solder it.\nLeft and right are mirrored.", position="lower_left",
               font_size=13, color="#333333")
    p.set_background("#e9e9e9")

    # from below, rear edge at the top of the picture, like the SVG diagram
    shoot(p, out / "wiring.png", (0, 0, -400), (0, 0, 5), up=(0, 1, 0), zoom=1.45)


def main():
    out = Path("out/renders")
    out.mkdir(parents=True, exist_ok=True)
    printed, bought = build()
    hero(printed, bought, out)
    exploded(printed, bought, out)
    cutaway(printed, bought, out)
    cutaway(printed, bought, out, pressed=True)
    wiring(printed, bought, out)


if __name__ == "__main__":
    main()
