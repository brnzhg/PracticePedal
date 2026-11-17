"""Build every part, run fit checks, and export STEP/STL/drawings.

    uv run python -m pedal_cad.build            # everything
    uv run python -m pedal_cad.build --no-draw  # skip the SVG drawings
"""

import math
import sys
from pathlib import Path

from build123d import Axis, Compound, Color, Pos, export_step, export_stl

from . import parts as pt
from .params import P

OUT = Path(__file__).resolve().parent.parent / "out"


def vol(a, b):
    c = a & b
    try:
        return c.volume
    except Exception:
        return 0.0


def flip(part):
    """As-used -> print orientation (upside down, resting on z=0)."""
    f = part.rotate(Axis.X, 180)
    bb = f.bounding_box()
    return Pos(-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z) * f


def build():
    p = P
    printed = {
        "tray": pt.make_tray(p),
        "sled": pt.make_sled(p),
        "top": pt.make_top(p),
        "riser": pt.make_riser(p),
    }
    bought = {
        "choc_left": pt.make_choc(p, p.switch_xs[0]),
        "choc_center": pt.make_choc(p, p.switch_xs[1]),
        "choc_right": pt.make_choc(p, p.switch_xs[2]),
        "nano": pt.make_nano(p),
        "battery": pt.make_battery(p),
        "power_switch": pt.make_power_switch(p),
        "stop_pad": pt.make_stop_pad(p),
    }
    return printed, bought


def checks(printed, bought):
    p = P
    ok = True

    def report(label, v, limit=0.5):
        nonlocal ok
        bad = v > limit
        ok &= not bad
        print(f"  {'FAIL' if bad else 'ok  '} {label}: {v:.2f} mm^3")

    print("Solids:")
    for n, s in printed.items():
        bb = s.bounding_box()
        nsol = len(s.solids())
        print(
            f"  {n:6s} {bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:5.1f}  "
            f"vol {s.volume / 1000:6.1f} cm^3  solids={nsol}"
        )
        if nsol != 1:
            ok = False
            print(f"  FAIL {n} is not a single solid")

    print("Interference at rest:")
    names = list(printed)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if {a, b} == {"top", "riser"}:
                continue  # pegs are a glued fit
            report(f"{a} / {b}", vol(printed[a], printed[b]))
    for bn, bs in bought.items():
        for a in names:
            if bn.startswith("choc") and a == "sled":
                continue  # clip-in fit, checked by dimension
            report(f"{a} / {bn}", vol(printed[a], bs), 0.3)

    print("Interference fully pressed (each key at the stop, pad uncompressed):")
    fixed = printed["tray"] + printed["sled"]
    for (name, *_), x in zip(pt.keys(p), p.switch_xs):
        key = printed["top"] & pt.key_region(p, name)
        if name == "center":
            key = key + printed["riser"]
        moved = pt.press(key, p, name)
        report(f"{name} key / tray+sled", vol(moved, fixed))
        report(f"{name} key / pad", vol(moved, bought["stop_pad"]), 2.0)
        over = pt.press(key, p, name, 1.0 + 0.3 / (p.stop_angle * (p.hinge_y - p.stop_y)))
        report(f"{name} key +0.3mm overtravel / sled", vol(over, printed["sled"]), 1.0)
        sw = pt.make_choc(p, x, pressed=p.stop_travel)
        report(f"{name} key / pressed switch", vol(moved, sw), 1.5)  # tilt of the pad on the stem

    print("Numbers:")
    th = p.stop_angle
    print(f"  total height {p.top_z:.1f} mm (riser top {p.top_z + p.riser_h:.1f})")
    print(f"  stop angle {math.degrees(th):.2f} deg, front edge drop {th * (p.hinge_y + p.D / 2):.2f} mm")
    print(f"  stem travel at stop {p.stop_travel:.2f} (actuates {p.choc_actuation}, bottoms {p.choc_travel})")
    for name, x0, x1, ft in pt.keys(p):
        w = x1 - x0
        for mat, E in (("PETG", 2000.0), ("PLA", 3300.0)):
            k = E * w * ft**3 / 12 / p.flex_len            # N*mm/rad
            arm = p.hinge_y + 42.0                         # toe ~9 mm from the front
            f_flex = k * th / arm
            sigma = E * ft * th / (2 * p.flex_len)
            print(
                f"  {name:6s} {mat}: hinge adds {f_flex * 102:4.0f} gf at the toe, "
                f"hinge stress {sigma:4.1f} MPa"
            )
    return ok


def export(printed, bought, draw=True):
    OUT.mkdir(exist_ok=True)
    (OUT / "stl").mkdir(exist_ok=True)
    (OUT / "step").mkdir(exist_ok=True)
    flipped = {"sled", "top", "riser"}
    for n, s in printed.items():
        ps = flip(s) if n in flipped else s
        export_stl(ps, str(OUT / "stl" / f"{n}.stl"), tolerance=0.01, angular_tolerance=0.1)
        export_step(s, str(OUT / "step" / f"{n}.step"))
    colors = {"tray": "DimGray", "sled": "Orange", "top": "SteelBlue", "riser": "Tomato"}
    kids = []
    for n, s in {**printed, **bought}.items():
        if s.volume <= 0:
            continue
        s.label = n
        s.color = Color(colors.get(n, "LightGray"))
        kids.append(s)
    asm = Compound(label="practice_pedal", children=kids)
    export_step(asm, str(OUT / "step" / "assembly.step"))
    if draw:
        from .draw import draw_all

        draw_all(printed, bought, OUT)


def main():
    printed, bought = build()
    ok = checks(printed, bought)
    export(printed, bought, draw="--no-draw" not in sys.argv)
    print("\nALL CHECKS PASSED" if ok else "\nCHECKS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
