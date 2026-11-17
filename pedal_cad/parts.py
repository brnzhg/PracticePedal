"""Printed parts and stand-in components for the PracticePedal.

Everything is modelled in the as-used position (see params.py). build.py
flips parts into their print orientation on export.
"""

from build123d import (
    Axis,
    Box,
    Cone,
    Cylinder,
    Part,
    Plane,
    Polygon,
    Pos,
    Rectangle,
    RectangleRounded,
    chamfer,
    extrude,
    fillet,
    offset,
)

from .params import Params


# ---------------------------------------------------------------- helpers
def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(
        x1 - x0, y1 - y0, z1 - z0
    )


def cyl(x, y, z0, z1, d):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(d / 2, z1 - z0)


def outline(p: Params, inset=0.0):
    return RectangleRounded(
        p.W - 2 * inset, p.D - 2 * inset, max(p.corner_r - inset, 0.6)
    )


def slab(p, inset, z0, z1):
    return Pos(0, 0, z0) * extrude(outline(p, inset), z1 - z0)


def ring(p, in0, in1, z0, z1):
    return slab(p, in0, z0, z1) - slab(p, in1, z0 - 1, z1 + 1)


def prism_yz(pts, x0, x1):
    """Extrude a (y, z) polygon along X from x0 to x1."""
    return Pos(x0, 0, 0) * extrude(Plane.YZ * Polygon(*pts, align=None), x1 - x0, dir=(1, 0, 0))


def prism_xz(pts, y0, y1):
    """Extrude an (x, z) polygon along Y from y0 to y1."""
    return Pos(0, y0, 0) * extrude(Plane.XZ * Polygon(*pts, align=None), y1 - y0, dir=(0, 1, 0))


def keys(p: Params):
    """(name, x0, x1, hinge thickness) for the three moving keys."""
    return (
        ("left", -p.pedal_x1, -p.pedal_x0, p.flex_t),
        ("center", -p.center_x1, p.center_x1, p.center_flex_t),
        ("right", p.pedal_x0, p.pedal_x1, p.flex_t),
    )


# ---------------------------------------------------------------- tray
def make_tray(p: Params) -> Part:
    hw, hd = p.W / 2, p.D / 2
    floor = slab(p, 0, 0, p.floor_t)
    floor = chamfer(floor.edges().group_by(Axis.Z)[0], 0.6)
    t = floor + ring(p, 0, p.wall, p.floor_t, p.sled_top)

    # thick front wall; the middle part rises to become the pedal down-stop
    env = slab(p, 0, 0, 40)
    t += box(-hw, hw, -hd, -hd + p.front_wall, p.floor_t, p.sled_top) & env
    xr = hw - p.rim_w - 0.4
    t += box(-xr, xr, -hd, -hd + p.front_wall, p.sled_top - 0.1, p.stop_z)

    # tongue that registers the top shell (rear, sides, rim fronts)
    tongue = ring(
        p, p.wall / 2 + p.lap_gap, p.wall, p.sled_top - 0.1, p.sled_top + p.lap_h
    )
    tongue -= box(-xr - 0.6, xr + 0.6, -hd - 1, -hd + p.front_wall + 3, 0, 40)
    for x, y in p.screws:
        tongue -= cyl(x, y, 0, 40, p.boss_d + 0.6)
    tongue -= box(-p.nano_ch_w / 2 - 0.3, p.nano_ch_w / 2 + 0.3, 0, hd + 1, 0, 40)
    t += tongue

    # screws: clearance hole + countersink from below
    for x, y in p.screws:
        t -= cyl(x, y, -1, p.floor_t + 1, p.screw_clear_d)
        t -= Pos(x, y, p.csk_depth / 2) * Cone(
            p.csk_d / 2, p.screw_clear_d / 2, p.csk_depth
        )
        t -= cyl(x, y, -1, 0.01, p.csk_d)

    # USB-C: open-topped notch for the shell + inside rebate for the PCB end
    z_usb0 = p.nano_zc - p.usb_h / 2 - 0.6
    uw = p.usb_w / 2 + 0.35
    t -= box(-uw, uw, hd - p.wall - 1, hd + 1, z_usb0, 40)
    t -= box(
        -p.nano_ch_w / 2 - 0.1,
        p.nano_ch_w / 2 + 0.1,
        hd - p.wall - 1,
        p.nano_y1 + 0.15,
        z_usb0 - 1.2,
        40,
    )

    # power switch: finger scoop outside, lever slot through the thinned wall
    zc = p.psw_zc
    t -= box(
        p.psw_x - p.psw_scoop_l / 2,
        p.psw_x + p.psw_scoop_l / 2,
        hd - p.psw_scoop_depth,
        hd + 1,
        zc - p.psw_scoop_h / 2,
        zc + p.psw_scoop_h / 2,
    )
    t -= box(
        p.psw_x - p.psw_slot_l / 2,
        p.psw_x + p.psw_slot_l / 2,
        hd - p.wall - 1,
        hd + 1,
        zc - p.psw_slot_h / 2,
        zc + p.psw_slot_h / 2,
    )

    for x, y in p.feet:
        t -= cyl(x, y, -1, p.foot_recess, p.foot_d)
    return t


# ---------------------------------------------------------------- sled
def sled_outline(p: Params):
    sx = p.sled_x
    yc = (p.sled_y_front_rim + p.sled_y_rear) / 2
    sk = Pos(0, yc) * Rectangle(2 * sx, p.sled_y_rear - p.sled_y_front_rim)
    sk = sk & outline(p, p.wall + p.fit)
    # trough at the front for the pedal lips
    ty = p.sled_y_front
    sk -= Pos(0, ty - 10) * Rectangle(2 * p.trough_x, 20)
    return sk


def make_sled(p: Params) -> Part:
    z0, zp, zt = p.sled_z0, p.plate_bot, p.sled_top
    sk = sled_outline(p)
    s = Pos(0, 0, z0) * extrude(sk, zt - z0)
    s -= Pos(0, 0, z0 - 1) * extrude(offset(sk, amount=-p.sled_wall), zp - z0 + 1)

    def rib(x, y0, y1):
        return box(x - p.rib_t / 2, x + p.rib_t / 2, y0, y1, z0, zp)

    yf = p.sled_y_front
    # screw columns
    x, y = p.screws[0]
    add = cyl(x, y, z0, zp, p.column_d)
    for x, y in p.screws[1:]:
        add += cyl(x, y, z0, zp, p.column_d)
    # ribs under the pedal ribs (overload path to the floor) + centre ribs
    off = p.pedal_rib_offset
    notch = box(-1, 1, -24, -17, z0 - 3, z0 - 2)
    for sgn in (-1, 1):
        for dx in (-off, off):
            add += rib(sgn * (p.pedal_xc + dx), yf, p.batt_y0 - 1.0)
        xc_r = sgn * (p.center_x1 + p.slot_w / 2)
        add += rib(xc_r, yf, p.latch_tip_y)
        for x in (sgn * (p.pedal_xc - off), xc_r):
            notch += box(x - 2, x + 2, -24, -17, z0 - 1, z0 + 3.0)

    # battery pocket walls
    bw = 1.2
    add += box(
        p.batt_x0 - bw, p.batt_x1 + bw, p.batt_y0 - bw, p.batt_y1 + bw, z0, zp
    ) - box(p.batt_x0, p.batt_x1, p.batt_y0, p.batt_y1, z0 - 1, zp + 1)

    # nice!nano channel walls
    cw = p.nano_ch_w / 2
    y_ch0 = p.latch_tip_y - 0.6
    z_slot = p.nano_pcb_z0 - 0.2          # PCB component face + clearance
    z_lip = z_slot - p.nano_lip - 0.6
    lips = ((p.nano_y0 + 0.6, p.nano_y0 + 8.6), (p.nano_y1 - 10.5, p.sled_y_rear))
    for sgn in (-1, 1):
        x_in, x_out = sgn * cw, sgn * (cw + p.sled_wall)
        xa, xb = min(x_in, x_out), max(x_in, x_out)
        add += box(xa, xb, y_ch0, p.sled_y_rear, z_slot, zp)
        for ya, yb in lips:
            add += box(xa, xb, ya, yb, z_lip, zp)

    # power switch side walls
    for sgn in (-1, 1):
        xw = p.psw_x + sgn * (p.psw_body_l / 2 + 0.15)
        add += box(
            min(xw, xw + sgn * 1.2),
            max(xw, xw + sgn * 1.2),
            p.sled_y_rear - p.sled_wall - p.psw_body_d,
            p.sled_y_rear - p.sled_wall + 0.1,
            z0,
            zp,
        )

    add = add & (Pos(0, 0, z0) * extrude(sk, zt - z0))
    s += add
    s -= notch

    # battery: thin roof + lead exit towards the centre
    s -= box(p.batt_x0, p.batt_x1, p.batt_y0, p.batt_y1, z0 - 1, zt - p.thin_roof)
    s -= box(p.batt_x1 - 0.5, p.batt_x1 + bw + 0.5, 25, 32, z0 - 1, zp)

    # nice!nano: thin roof, open rear, rails, lips, latch tongue, slide-in window
    zr = p.nano_roof_z
    s -= box(-cw, cw, y_ch0, p.sled_y_rear + 1, z0 - 1, zr)
    s -= box(-cw, cw, p.window_y0, y_ch0, z0 - 1, zt + 1)
    lp = p.nano_lip
    for sgn in (-1, 1):
        xa, xb = sorted((sgn * cw, sgn * (cw - 0.9)))
        s += box(xa, xb, y_ch0, p.sled_y_rear, p.nano_pcb_z1, zr)
        tri = (
            (sgn * cw, z_slot),
            (sgn * (cw - lp), z_slot - lp),
            (sgn * (cw - lp), z_lip),
            (sgn * cw, z_lip),
        )
        for ya, yb in lips:
            s += prism_xz(tri, ya, yb)
    tw, ty0, ty1 = 3.0, p.latch_tip_y, p.nano_y0 + 17.0
    for sgn in (-1, 1):
        xa, xb = sorted((sgn * tw, sgn * (tw + 0.6)))
        s -= box(xa, xb, ty0 - 1, ty1, zr - 1, zt + 1)
    yb = p.nano_y0 - 0.3                   # stop face behind the PCB end
    zb = p.nano_pcb_z0 + 0.1
    s += prism_yz(((ty0, zr), (yb, zr), (yb, zb), (yb - 0.5, zb)), -2.5, 2.5)

    # power switch: thin the rear wall, lever slot
    xa, xb = p.psw_x - p.psw_body_l / 2 - 0.15, p.psw_x + p.psw_body_l / 2 + 0.15
    s -= box(xa, xb, p.sled_y_rear - p.sled_wall - 0.1, p.sled_y_rear - 0.8, z0 - 1, zp)
    s -= box(
        p.psw_x - p.psw_slot_l / 2,
        p.psw_x + p.psw_slot_l / 2,
        p.sled_y_rear - 1,
        p.sled_y_rear + 1,
        p.psw_zc - p.psw_slot_h / 2,
        p.psw_zc + p.psw_slot_h / 2,
    )

    # switch cut-outs and screw holes
    c = p.choc_cutout / 2
    for x in p.switch_xs:
        s -= box(x - c, x + c, p.switch_y - c, p.switch_y + c, zp - 1, zt + 1)
    for x, y in p.screws:
        s -= cyl(x, y, z0 - 1, zt + 1, p.screw_clear_d + 0.2)
    return s


# ---------------------------------------------------------------- top shell
def make_top(p: Params) -> Part:
    hw, hd = p.W / 2, p.D / 2
    zs, zt = p.skin_bot, p.top_z
    skin = slab(p, 0, zs, zt)
    skin = chamfer(skin.edges().group_by(Axis.Z)[-1], p.top_chamfer)

    # skirt on the rear, the sides and the rim fronts; lower part is half
    # thickness so the tray tongue fits inside it
    xr = hw - p.rim_w
    skirt = ring(p, 0, p.wall, p.sled_top, zs + 0.1)
    skirt -= box(-xr, xr, -hd - 1, -hd + p.front_wall + 3, 0, 40)
    skirt -= ring(p, p.wall / 2, p.wall + 0.5, p.sled_top - 1, p.sled_top + p.lap_h + 0.2)
    top = skin + skirt

    for x, y in p.screws:
        top += cyl(x, y, p.sled_top, zs + 0.1, p.boss_d)

    for name, x0, x1, ft in keys(p):
        xc = (x0 + x1) / 2
        # actuator pad over the switch stem
        top += cyl(xc, p.switch_y, zs - p.act_boss_h, zs + 0.1, p.act_boss_d)
        # front lip
        top += box(x0 + 0.5, x1 - 0.5, p.lip_y0, p.lip_y1, zs - p.lip_h, zs + 0.1)
        # wedge ribs: bottom edge parks rib_clear above the sled at full press
        if name != "center":
            def zb(y):
                return p.sled_top + p.rib_clear + p.stop_angle * (p.hinge_y - y)

            ya, yb = p.lip_y1 - 0.1, p.batt_y0 - 1.5
            pts = ((ya, zs + 0.1), (ya, zb(ya)), (yb, zb(yb)), (yb + 3, zs + 0.1))
            for dx in (-p.pedal_rib_offset, p.pedal_rib_offset):
                x = xc + dx
                top += prism_yz(pts, x - p.pedal_rib_w / 2, x + p.pedal_rib_w / 2)
        # living hinge: groove on the underside with 45 degree run-outs
        g = p.skin_t - ft
        y0, y1 = p.flex_front_y, p.flex_rear_y
        groove = ((y0 - g, zs - 0.1), (y0, zs + g), (y1, zs + g), (y1 + g, zs - 0.1))
        top -= prism_yz(groove, x0 - 0.01, x1 + 0.01)

    # slots that free the keys
    sw = p.slot_w
    for xs in (
        -p.pedal_x1 - sw / 2,
        -p.pedal_x0 + sw / 2,
        p.pedal_x0 - sw / 2,
        p.pedal_x1 + sw / 2,
    ):
        top -= box(xs - sw / 2, xs + sw / 2, -hd - 1, p.flex_rear_y, zs - 1, zt + 1)
        top -= cyl(xs, p.flex_rear_y, zs - 1, zt + 1, sw)

    # heat-set insert holes
    for x, y in p.screws:
        top -= cyl(x, y, p.sled_top - 1, p.sled_top + p.insert_hole_depth, p.insert_hole_d)
    # riser peg holes
    for y in p.peg_ys:
        top -= cyl(0, y, zs - 1, zt + 1, p.peg_d + 0.3)
    return top


def make_riser(p: Params) -> Part:
    y0 = p.riser_front_y
    r = box(-p.riser_w / 2, p.riser_w / 2, y0, y0 + p.riser_len, p.top_z, p.top_z + p.riser_h)
    r = fillet(r.edges().filter_by(Axis.Z), 3.0)
    r = chamfer(r.edges().group_by(Axis.Z)[-1], 1.5)
    for y in p.peg_ys:
        r += cyl(0, y, p.top_z - p.peg_h, p.top_z + 0.1, p.peg_d)
    return r


# ---------------------------------------------------------------- stand-ins
def make_choc(p: Params, x, pressed=0.0) -> Part:
    y, zt = p.switch_y, p.sled_top
    c = box(x - 6.9, x + 6.9, y - 6.9, y + 6.9, zt - p.choc_below_plate, zt)
    c += box(x - 7.5, x + 7.5, y - 7.5, y + 7.5, zt, zt + p.choc_housing_above)
    c += box(x - 5.1, x + 5.1, y - 2.25, y + 2.25, zt, zt + p.choc_above_plate - pressed)
    zpin = zt - p.choc_below_plate
    c += cyl(x, y + 5.9, zpin - p.choc_pin_len, zpin, 1.2)
    c += cyl(x + 5.0, y + 3.8, zpin - p.choc_pin_len, zpin, 1.2)
    return c


def make_nano(p: Params) -> Part:
    w = p.nano_w / 2
    n = box(-w, w, p.nano_y0, p.nano_y1, p.nano_pcb_z0, p.nano_pcb_z1)
    n += box(
        -p.usb_w / 2,
        p.usb_w / 2,
        p.nano_y1 - 6.2,
        p.nano_y1 + p.usb_overhang,
        p.nano_zc - p.usb_h / 2,
        p.nano_zc + p.usb_h / 2,
    )
    # components (chip, antenna...) on the side facing the floor
    n += box(-6, 6, p.nano_y0 + 1, p.nano_y1 - 8, p.nano_pcb_z0 - 1.0, p.nano_pcb_z0)
    return n


def make_battery(p: Params) -> Part:
    # 503450: 50 x 34 x 5
    xc, yc = (p.batt_x0 + p.batt_x1) / 2, (p.batt_y0 + p.batt_y1) / 2
    z1 = p.sled_top - p.thin_roof - 0.3
    return box(xc - 25, xc + 25, yc - 17, yc + 17, z1 - 5.0, z1)


def make_power_switch(p: Params) -> Part:
    x, zc = p.psw_x, p.psw_zc
    y1 = p.sled_y_rear - 0.8
    t = 4.4
    b = box(x - 4.3, x + 4.3, y1 - 3.6, y1, zc - t / 2, zc + t / 2)
    b += box(x - 2.0, x, y1, y1 + 3.0, zc - 0.75, zc + 0.75)        # lever
    for dx in (-2.5, 0, 2.5):
        b += box(x + dx - 0.4, x + dx + 0.4, y1 - 3.6 - 3.0, y1 - 3.6, zc - 0.15, zc + 0.15)
    return b


def make_stop_pad(p: Params) -> Part:
    if p.stop_pad_t <= 0:
        return Part()
    xr = p.W / 2 - p.rim_w - 0.4
    return box(-xr, xr, -p.D / 2 + 0.3, -p.D / 2 + p.front_wall - 0.3, p.stop_z, p.stop_z + p.stop_pad_t)


def key_region(p: Params, name) -> Part:
    """Volume containing one moving key (forward of its hinge)."""
    for n, x0, x1, _ in keys(p):
        if n == name:
            return box(x0, x1, -p.D / 2 - 1, p.flex_front_y, 0, 60)
    raise KeyError(name)


def press(part, p: Params, name, fraction=1.0):
    """Rotate geometry about a key's hinge axis by `fraction` of the stop angle."""
    import math

    ft = {n: t for n, _, _, t in keys(p)}[name]
    axis = Axis((0, p.hinge_y, p.top_z - ft / 2), (1, 0, 0))
    return part.rotate(axis, math.degrees(p.stop_angle) * fraction)
