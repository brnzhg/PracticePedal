"""Hidden-line SVG drawings of the parts and the assembly."""

from build123d import Axis, Compound, ExportSVG, LineType, Pos, Unit

from . import parts as pt
from .params import P


def svg(shapes, path, origin, up=(0, 0, 1), look_at=None, hidden=False):
    comp = Compound(children=[s for s in shapes if s.volume > 0])
    look_at = look_at or comp.bounding_box().center()
    vis, hid = comp.project_to_viewport(origin, up, look_at)
    ex = ExportSVG(unit=Unit.MM, scale=4, line_weight=0.18)
    ex.add_layer("vis", line_weight=0.18)
    ex.add_layer("hid", line_weight=0.08, line_type=LineType.ISO_DOT)
    ex.add_shape(vis, layer="vis")
    if hidden:
        ex.add_shape(hid, layer="hid")
    ex.write(str(path))


def section(shapes, x, side=1):
    """Keep the half of each shape on the far side of the plane X = x."""
    keep = pt.box(x - 200, x, -200, 200, -50, 100) if side > 0 else pt.box(x, x + 200, -200, 200, -50, 100)
    out = []
    for s in shapes:
        c = s & keep
        if c.volume > 0:
            out.append(c)
    return out


def draw_all(printed, bought, out):
    d = out / "drawings"
    d.mkdir(exist_ok=True)
    p = P
    everything = list(printed.values()) + list(bought.values())

    svg(everything, d / "assembly_iso.svg", (-180, -260, 200))
    svg(everything, d / "assembly_rear.svg", (120, 300, 120))
    svg(everything, d / "assembly_top.svg", (0, 0, 400), up=(0, 1, 0))

    # exploded
    ex = [
        printed["tray"],
        Pos(0, 0, 30) * printed["sled"],
        Pos(0, 0, 70) * printed["top"],
        Pos(0, 0, 95) * printed["riser"],
    ] + [Pos(0, 0, 30 if "choc" not in n else 48) * s for n, s in bought.items() if n != "stop_pad"]
    svg(ex, d / "exploded.svg", (-220, -300, 260))

    # sections, looking along -X (front of the pedal on the left)
    svg(section(everything, p.pedal_xc), d / "section_pedal.svg", (500, 0, 9), look_at=(0, 0, 9))
    svg(section(everything, 0.0), d / "section_center.svg", (500, 0, 9), look_at=(0, 0, 9))
    pressed = [printed["tray"], printed["sled"], bought["stop_pad"],
               pt.make_choc(p, p.pedal_xc, pressed=p.stop_travel),
               printed["top"] - pt.key_region(p, "right"),
               pt.press(printed["top"] & pt.key_region(p, "right"), p, "right")]
    svg(section(pressed, p.pedal_xc), d / "section_pedal_pressed.svg", (500, 0, 9), look_at=(0, 0, 9))

    # undersides (as you see them while wiring / as printed)
    svg([printed["sled"]] + [bought[k] for k in ("nano", "battery", "power_switch", "choc_left", "choc_center", "choc_right")],
        d / "sled_wiring_side.svg", (0, 0, -400), up=(0, 1, 0), hidden=False)
    svg([printed["sled"]], d / "sled_underside_iso.svg", (160, -220, -220), up=(0, 0, -1))
    svg([printed["top"]], d / "top_underside_iso.svg", (160, -260, -200), up=(0, 0, -1))
    svg([printed["tray"]], d / "tray_iso.svg", (-160, -240, 220))
