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


def wiring_diagram(bought, path):
    """Colour wiring diagram of the sled seen from below (the side you solder on).

    Drawn by hand from part positions rather than projected, so it can carry labels.
    Looking from below mirrors left and right: the left pedal's switch is on the right.
    """
    p = P
    s = 7.0                     # px per mm
    mx, my = 40, 70             # margins
    W, D = p.W, p.D
    legend_w = 330

    def pt_(x, y):              # model (from below, rear up) -> svg px
        return mx + (W / 2 - x) * s, my + (D / 2 - y) * s

    def rect(bb_or_xy, fill, stroke="#333", rx=2, extra=""):
        x0, x1, y0, y1 = bb_or_xy
        ax, ay = pt_(x1, y1)
        bx, by = pt_(x0, y0)
        return (f'<rect x="{ax:.1f}" y="{ay:.1f}" width="{bx - ax:.1f}" height="{by - ay:.1f}" '
                f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1.2" {extra}/>')

    def text(x, y, t, size=13, anchor="middle", weight="normal", fill="#111"):
        px, py = pt_(x, y)
        return (f'<text x="{px:.1f}" y="{py:.1f}" font-size="{size}" text-anchor="{anchor}" '
                f'font-weight="{weight}" fill="{fill}" dominant-baseline="middle">{t}</text>')

    def wire(pts, color, width=2.6):
        d = " ".join(f"{'M' if i == 0 else 'L'}{pt_(*q)[0]:.1f},{pt_(*q)[1]:.1f}" for i, q in enumerate(pts))
        return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" '
                f'stroke-linejoin="round" stroke-linecap="round"/>')

    def dot(x, y, color, r=4):
        px, py = pt_(x, y)
        return f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r}" fill="{color}" stroke="#111" stroke-width="0.8"/>'

    def bb(part):
        b = part.bounding_box()
        return b.min.X, b.max.X, b.min.Y, b.max.Y

    el = []
    # sled
    sx, yr, yf = p.sled_x, p.sled_y_rear, p.sled_y_front_rim
    el.append(rect((-sx, sx, yf, yr), "#f6efe4", "#8a7a63", rx=10))
    # rib notches the switch wires pass through
    el.append(rect((-sx + 2, sx - 2, -24, -17), "#ece2d2", "none", rx=1))
    el.append(text(-sx + 4, -15.5, "wire channel (notches in the ribs)", 11, "end", fill="#8a7a63"))

    # battery
    b = bb(bought["battery"])
    el.append(rect(b, "#cfe3f7", "#2f6ea8", rx=4))
    bcx, bcy = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2
    el.append(text(bcx, bcy + 3, "BATTERY", 18, weight="bold", fill="#2f6ea8"))
    el.append(text(bcx, bcy - 1.5, "LiPo in its pocket, leads exit", 12, fill="#2f6ea8"))
    el.append(text(bcx, bcy - 4, "towards the nice!nano", 12, fill="#2f6ea8"))

    # power switch
    ps = bb(bought["power_switch"])
    el.append(rect(ps, "#e0e0e0", "#555", rx=1))
    el.append(text(ps[0] - 1.5, (ps[2] + ps[3]) / 2, "power switch", 12, "start", "bold"))

    # nice!nano
    nb = bb(bought["nano"])
    el.append(rect((-p.nano_w / 2, p.nano_w / 2, p.nano_y0, p.nano_y1), "#2e2e4f", "#111", rx=2))
    el.append(rect((-p.usb_w / 2, p.usb_w / 2, p.nano_y1 - 6.2, nb[3]), "#b8b8b8", "#555", rx=1))
    el.append(text(0, nb[3] + 3, "USB-C", 11, weight="bold"))

    # nano pins: 2 x 12 at 2.54 mm, rows 15.24 apart. Seen from the component side
    # with USB up, the left row (+X here) is D1 D0 GND GND D2 D3 D4 ...,
    # the right row is B+ B- RST VCC ...
    left_row = ["D1", "D0", "GND", "GND", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"]
    right_row = ["B+", "B-", "RST", "VCC", "D21", "D20", "D19", "D18", "D15", "D14", "D16", "D10"]
    px_l, px_r = 7.62, -7.62
    pin_y = [p.nano_y1 - 2.53 - 2.54 * i for i in range(12)]
    used = {(px_l, 3), (px_l, 4), (px_l, 5), (px_l, 6), (px_r, 0), (px_r, 1)}
    for names, x in ((left_row, px_l), (right_row, px_r)):
        for i, (n, y) in enumerate(zip(names, pin_y)):
            px, py = pt_(x, y)
            on = (x, i) in used
            col = "#f2c84b" if on else "#8a7d4a"
            el.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="{col}" stroke="#111" stroke-width="0.6"/>')
            if on:   # label inside the board, towards the centre
                tx = x - 1.6 if x > 0 else x + 1.6
                el.append(text(tx, y, n, 10, "start" if x > 0 else "end", "bold", "#fff"))
    el.append(text(0, pin_y[8], "nice!nano", 12, weight="bold", fill="#fff"))
    el.append(text(0, pin_y[10], "parts up", 10, fill="#ccc"))

    # switches (left pedal is at -X, which is on the right when seen from below)
    cols = {"left": "#2a9d4b", "center": "#1f6fd1", "right": "#9b3fc4"}
    pin_of = {"left": "D2", "center": "D3", "right": "D4"}
    label = {"left": "LEFT pedal switch", "center": "CENTRE switch", "right": "RIGHT pedal switch"}
    y_sig, y_gnd = -19.0, -22.5
    gnd_pin_y = pin_y[3]
    for name, x in zip(("left", "center", "right"), p.switch_xs):
        y = p.switch_y
        el.append(rect((x - 7.5, x + 7.5, y - 7.5, y + 7.5), "#fff", "#333", rx=1.5))
        el.append(text(x, y - 11, label[name], 12, weight="bold", fill=cols[name]))
        a, g = (x, y + 5.9), (x + 5.0, y + 3.8)
        # signal: pin -> channel -> up the +X side of the nano -> Dn
        yp = pin_y[left_row.index(pin_of[name])]
        xv = px_l + 4.5 + {"left": 0, "center": 1.5, "right": 3.0}[name]
        el.append(wire([a, (a[0], y_sig + {"left": 0, "center": 0.8, "right": 1.6}[name]),
                        (xv, y_sig + {"left": 0, "center": 0.8, "right": 1.6}[name]), (xv, yp), (px_l, yp)],
                       cols[name]))
        el.append(dot(*a, cols[name]))
        el.append(dot(*g, "#222"))
    # ground chain: switch to switch along the channel, then to a GND pin
    gs = [(x + 5.0, p.switch_y + 3.8) for x in p.switch_xs]
    for g in gs:
        el.append(wire([g, (g[0], y_gnd)], "#222"))
    xg = px_l + 10.5
    el.append(wire([(gs[0][0], y_gnd), (gs[2][0], y_gnd)], "#222"))
    el.append(wire([(xg, y_gnd), (xg, gnd_pin_y), (px_l, gnd_pin_y)], "#222"))

    # battery and power switch
    lead_y = 28.5
    bplus = (p.batt_x1, lead_y + 1.2)
    bminus = (p.batt_x1, lead_y - 1.2)
    sw_c = (p.psw_x, ps[2])
    sw_o = (p.psw_x + 2.5, ps[2])
    yb = pin_y[0]
    el.append(wire([bplus, (bplus[0] + 2, bplus[1]), (bplus[0] + 2, sw_c[1] - 2), (sw_c[0], sw_c[1] - 2), sw_c], "#d62828"))
    el.append(wire([sw_o, (sw_o[0], sw_o[1] - 4.5), (px_r - 3.5, sw_o[1] - 4.5), (px_r - 3.5, yb), (px_r, yb)], "#e76f51"))
    el.append(wire([bminus, (px_r - 1.8, bminus[1]), (px_r - 1.8, pin_y[1]), (px_r, pin_y[1])], "#222"))
    for q, c in ((bplus, "#d62828"), (bminus, "#222"), (sw_c, "#d62828"), (sw_o, "#e76f51")):
        el.append(dot(*q, c, 3.2))

    # edge labels
    el.append(text(0, D / 2 + 6.5, "REAR EDGE (USB and power switch poke out here)", 14, weight="bold"))
    el.append(text(0, yf - 4.5, "FRONT EDGE (toe end of the pedals)", 14, weight="bold"))

    # legend
    gx = mx + W * s + 30
    rows = [
        ("#2a9d4b", "Left pedal switch  →  D2"),
        ("#1f6fd1", "Centre switch  →  D3"),
        ("#9b3fc4", "Right pedal switch  →  D4"),
        ("#222", "Other pin of every switch  →  GND"),
        ("#d62828", "Battery +  →  power switch centre pin"),
        ("#e76f51", "Power switch outer pin  →  B+"),
        ("#222", "Battery −  →  B− (GND)"),
    ]
    lg = [f'<text x="{gx}" y="{my + 6}" font-size="16" font-weight="bold">Wiring</text>']
    for i, (c, t) in enumerate(rows):
        y = my + 36 + i * 28
        lg.append(f'<line x1="{gx}" y1="{y}" x2="{gx + 34}" y2="{y}" stroke="{c}" stroke-width="4" stroke-linecap="round"/>')
        lg.append(f'<text x="{gx + 44}" y="{y}" font-size="13" dominant-baseline="middle">{t}</text>')
    notes = [
        "You are looking at the UNDERSIDE of the sled,",
        "the way it sits on the bench while you solder.",
        "Left and right are mirrored: the LEFT pedal's",
        "switch is on the RIGHT of this picture.",
        "",
        "The nice!nano lies parts-side up (towards you),",
        "USB-C to the rear edge.",
        "",
        "Either pin of a key switch can be the signal one.",
        "Wire routes are a suggestion; pin positions on",
        "the nice!nano are drawn to scale.",
    ]
    for i, t in enumerate(notes):
        lg.append(f'<text x="{gx}" y="{my + 250 + i * 19}" font-size="12.5" fill="#444">{t}</text>')

    w_px = gx + legend_w
    h_px = pt_(0, yf - 9)[1]
    out = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_px:.0f}" height="{h_px:.0f}" '
        f'viewBox="0 0 {w_px:.0f} {h_px:.0f}" font-family="Helvetica, Arial, sans-serif">'
        f'<rect width="100%" height="100%" fill="#fff"/>' + "".join(el) + "".join(lg) + "</svg>"
    )
    path.write_text(out)


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
    wiring_diagram(bought, d / "wiring.svg")
    svg([printed["sled"]], d / "sled_underside_iso.svg", (160, -220, -220), up=(0, 0, -1))
    svg([printed["top"]], d / "top_underside_iso.svg", (160, -260, -200), up=(0, 0, -1))
    svg([printed["tray"]], d / "tray_iso.svg", (-160, -240, 220))
