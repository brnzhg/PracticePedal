"""All dimensions for the PracticePedal, in millimetres.

Coordinate system (as used, sitting on the floor):
  X  left/right, 0 at the centre
  Y  front/back, 0 at the centre; -Y is the edge nearest the player
  Z  up, 0 at the floor

Edit values here and re-run `uv run python -m pedal_cad.build`.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Params:
    # ---- envelope (AirTurn PED 500 is 152 x 102 x 18) ----
    W: float = 152.0
    D: float = 102.0
    corner_r: float = 6.0

    # ---- generic ----
    wall: float = 2.4            # outer wall thickness
    floor_t: float = 2.4         # tray floor (takes the M3 countersinks)
    front_wall: float = 5.0      # tray front wall; its top is the pedal down-stop
    fit: float = 0.25            # clearance between nested printed parts

    # ---- sled (switch plate + electronics carrier) ----
    cavity_h: float = 5.5        # wiring space below the switch plate
    plate_t: float = 1.3         # Choc clips need 1.2-1.3
    thin_roof: float = 0.8       # roof over battery / nice!nano
    sled_wall: float = 1.6
    rib_t: float = 1.6

    # ---- Kailh Choc v1 (PG1350) ----
    choc_cutout: float = 13.9    # nominal 13.8, +0.1 for FDM
    choc_above_plate: float = 5.8  # plate top to stem top, unpressed
    choc_housing_above: float = 2.8
    choc_below_plate: float = 2.2
    choc_pin_len: float = 3.0
    choc_travel: float = 3.0
    choc_actuation: float = 1.5

    # ---- top shell / pedals ----
    skin_t: float = 3.0
    back_strip: float = 14.0     # fixed strip behind the hinges
    flex_len: float = 8.0        # length of the thinned living hinge
    flex_t: float = 1.6          # side pedal hinge thickness  (force ~ t^3)
    center_flex_t: float = 2.0   # centre key hinge thickness (stiffer on purpose)
    slot_w: float = 1.0
    rim_w: float = 8.0           # fixed side rails
    center_w: float = 22.0       # centre key width
    top_chamfer: float = 1.0
    act_boss_h: float = 0.4      # pad under each pedal that touches the stem
    act_boss_d: float = 8.0
    stem_gap: float = 0.2        # free play before the pedal touches the stem
    lip_h: float = 6.0           # front lip under each pedal (hides the gap)
    lip_t: float = 1.6
    pedal_rib_w: float = 2.4
    pedal_rib_offset: float = 19.0  # ribs sit this far either side of the switch
    rib_clear: float = 0.4       # rib-to-sled gap when fully pressed

    # ---- press geometry ----
    switch_y: float = -33.0
    stop_travel: float = 2.2     # stem travel when the pedal hits the stop
    stop_pad_t: float = 1.0      # felt / foam strip on the stop (0 = none)

    # ---- centre riser ----
    riser_w: float = 19.0
    riser_len: float = 48.0
    riser_h: float = 7.0
    riser_front_y: float = -49.0
    peg_d: float = 4.0
    peg_h: float = 2.6
    peg_ys: tuple = (-41.5, -8.0)

    # ---- fasteners: 6x M3x12 countersunk + M3 heat-set inserts ----
    screw_clear_d: float = 3.4
    csk_d: float = 6.2
    csk_depth: float = 1.4
    boss_d: float = 7.5
    insert_hole_d: float = 4.0   # for M3 x 4-5 mm long, 4.6-5 mm OD inserts
    insert_hole_depth: float = 6.2
    column_d: float = 8.4
    lap_h: float = 1.5           # tray tongue that registers the top shell
    lap_gap: float = 0.15

    # ---- nice!nano v2 (measure yours; vendors quote 17.8-18.3 wide) ----
    nano_w: float = 18.3
    nano_pcb_l: float = 33.0
    nano_pcb_t: float = 1.6
    usb_overhang: float = 1.1    # USB-C shell past the PCB edge
    usb_w: float = 8.94
    usb_h: float = 3.26
    usb_recess: float = 0.0      # shell face behind the outer wall face
    nano_rail_h: float = 1.0     # stand-off between roof and PCB back
    nano_lip: float = 1.0

    # ---- battery pocket (fits up to a 503450, 1000 mAh) ----
    batt_l: float = 52.0         # along X
    batt_w: float = 35.5         # along Y
    batt_x1: float = -19.5       # pocket edge nearest the centre
    batt_y0: float = 1.5

    # ---- power switch: SS12D00G3 style mini slide switch ----
    psw_x: float = -40.0
    psw_body_l: float = 8.7      # along X
    psw_body_t: float = 4.5      # along Z (3.7-4.4 depending on vendor)
    psw_body_d: float = 4.7      # along Y
    psw_slot_l: float = 5.2
    psw_slot_h: float = 3.2
    psw_scoop_l: float = 13.0
    psw_scoop_h: float = 5.6
    psw_scoop_depth: float = 1.4

    # ---- feet ----
    foot_d: float = 12.4         # recess for 12 mm stick-on bumpers
    foot_recess: float = 0.4

    # ================= derived =================
    @property
    def sled_z0(self):
        return self.floor_t

    @property
    def plate_bot(self):
        return self.sled_z0 + self.cavity_h

    @property
    def sled_top(self):
        return self.plate_bot + self.plate_t

    @property
    def stem_top(self):
        return self.sled_top + self.choc_above_plate

    @property
    def skin_bot(self):
        return self.stem_top + self.stem_gap + self.act_boss_h

    @property
    def top_z(self):
        return self.skin_bot + self.skin_t

    # hinge
    @property
    def flex_rear_y(self):
        return self.D / 2 - self.back_strip

    @property
    def flex_front_y(self):
        return self.flex_rear_y - self.flex_len

    @property
    def hinge_y(self):
        return (self.flex_rear_y + self.flex_front_y) / 2

    @property
    def hinge_z(self):
        return self.top_z - self.flex_t / 2

    @property
    def stop_angle(self):
        """Pedal rotation (rad) at the stop."""
        return (self.stop_travel + self.stem_gap) / (self.hinge_y - self.switch_y)

    @property
    def stop_y(self):
        return -self.D / 2 + 0.3   # the pedal lands on the front edge of the pad first

    @property
    def stop_z(self):
        """Top of the tray front wall."""
        drop = self.stop_angle * (self.hinge_y - self.stop_y)
        return self.skin_bot - drop - self.stop_pad_t

    # plan layout
    @property
    def center_x1(self):
        return self.center_w / 2

    @property
    def pedal_x0(self):
        return self.center_x1 + self.slot_w

    @property
    def pedal_x1(self):
        return self.W / 2 - self.rim_w - self.slot_w

    @property
    def pedal_xc(self):
        return (self.pedal_x0 + self.pedal_x1) / 2

    @property
    def switch_xs(self):
        return (-self.pedal_xc, 0.0, self.pedal_xc)

    @property
    def lip_y0(self):
        return -self.D / 2 + self.front_wall + 0.3

    @property
    def lip_y1(self):
        return self.lip_y0 + self.lip_t

    @property
    def sled_x(self):
        return self.W / 2 - self.wall - self.fit

    @property
    def sled_y_rear(self):
        return self.D / 2 - self.wall - self.fit

    @property
    def sled_y_front_rim(self):
        return -self.D / 2 + self.front_wall + self.fit

    @property
    def sled_y_front(self):
        return self.lip_y1 + 0.8

    @property
    def trough_x(self):
        return self.W / 2 - self.rim_w - 0.1

    @property
    def screws(self):
        xs, xm = self.W / 2 - 4.0, 24.0
        yr, yf = self.D / 2 - 6.5, -self.D / 2 + 9.5
        return ((-xs, yr), (xs, yr), (-xm, yr), (xm, yr), (-xs, yf), (xs, yf))

    @property
    def feet(self):
        return ((-56, 34), (56, 34), (-56, -34), (56, -34))

    # nice!nano placement (component side faces the floor, USB at the rear wall)
    @property
    def nano_ch_w(self):
        return self.nano_w + 0.3

    @property
    def nano_roof_z(self):
        return self.sled_top - self.thin_roof

    @property
    def nano_pcb_z1(self):   # PCB back face (towards the roof)
        return self.nano_roof_z - self.nano_rail_h

    @property
    def nano_pcb_z0(self):
        return self.nano_pcb_z1 - self.nano_pcb_t

    @property
    def nano_zc(self):
        return (self.nano_pcb_z0 + self.nano_pcb_z1) / 2

    @property
    def nano_y1(self):       # PCB edge at the USB end
        return self.D / 2 - self.usb_recess - self.usb_overhang

    @property
    def nano_y0(self):
        return self.nano_y1 - self.nano_pcb_l

    @property
    def latch_tip_y(self):
        return self.nano_y0 - 3.1

    @property
    def window_y0(self):
        return self.latch_tip_y - 0.6 - (self.nano_pcb_l + 1.5)

    # battery
    @property
    def batt_x0(self):
        return self.batt_x1 - self.batt_l

    @property
    def batt_y1(self):
        return self.batt_y0 + self.batt_w

    @property
    def psw_zc(self):
        return self.plate_bot - self.psw_body_t / 2


P = Params()
