"""
Exact dimensional and geometric configuration for the
2024 Tesla Model S Plaid (Ultra Red PR01, 21" Arachnid, Sport Seats).

Coordinate System (1 Blender Unit = 1.0 meter):
  +X : Right (Passenger side, LHD)
  -X : Left (Driver side, LHD)
  +Y : Forward (Front nose tip at Y = +2.441 m)
  -Y : Rearward (Rear bumper crown at Y = -2.580 m)
  +Z : Up (Ground plane at Z = 0.000 m)
"""

import os

# Paths
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEXTURE_DIR = os.path.join(REPO_ROOT, "textures")
BLEND_DIR = os.path.join(REPO_ROOT, "blend")
RENDER_DIR = os.path.join(REPO_ROOT, "renders")

# Official 2023-2024 Tesla Model S Plaid Exterior Dimensions (meters)
LENGTH = 5.021                  # 5,021 mm
WHEELBASE = 2.960               # 2,960 mm
FRONT_OVERHANG = 0.961          # 961 mm
REAR_OVERHANG = 1.100           # 1,100 mm
WIDTH_BODY = 1.987              # 1,987 mm (at rear Plaid flared haunches)
WIDTH_HALF = WIDTH_BODY * 0.5   # 0.9935 m
WIDTH_MIRRORS = 2.189           # 2,189 mm (tip-to-tip)
HEIGHT = 1.430                  # 1,430 mm (medium/sport stance)
GROUND_CLEARANCE = 0.122        # 122 mm (sport low stance)

# Longitudinal axle and extremity coordinates (Y)
Y_FRONT_AXLE = WHEELBASE * 0.5          # +1.480 m
Y_REAR_AXLE = -WHEELBASE * 0.5          # -1.480 m
Y_FRONT_TIP = Y_FRONT_AXLE + FRONT_OVERHANG   # +2.441 m
Y_REAR_TIP = Y_REAR_AXLE - REAR_OVERHANG      # -2.580 m

# Staggered 21" Arachnid Wheels & Michelin Pilot Sport 4S Tires
# Front: 21x9.5J ET40 | 265/35 ZR21 -> OD = 533.4 + 185.5 = 718.9 mm
FRONT_RIM_DIAM = 21.0 * 0.0254          # 0.5334 m
FRONT_RIM_RAD = FRONT_RIM_DIAM * 0.5    # 0.2667 m
FRONT_RIM_WIDTH = 9.5 * 0.0254          # 0.2413 m
FRONT_TIRE_WIDTH = 0.265                # 265 mm
FRONT_TIRE_RAD = 0.3595                 # 359.5 mm unloaded
FRONT_TIRE_SQUAT = 0.0075               # 7.5 mm static load deflection
FRONT_WHEEL_Z = FRONT_TIRE_RAD - FRONT_TIRE_SQUAT  # 0.352 m
FRONT_TRACK = 1.690                     # 1,690 mm
FRONT_WHEEL_X = FRONT_TRACK * 0.5       # 0.845 m (outer tire face at 0.9775 m)

# Rear: 21x10.5J ET45 | 295/30 ZR21 -> OD = 533.4 + 177.0 = 710.4 mm
REAR_RIM_DIAM = 21.0 * 0.0254           # 0.5334 m
REAR_RIM_RAD = REAR_RIM_DIAM * 0.5      # 0.2667 m
REAR_RIM_WIDTH = 10.5 * 0.0254          # 0.2667 m
REAR_TIRE_WIDTH = 0.295                 # 295 mm
REAR_TIRE_RAD = 0.3552                  # 355.2 mm unloaded
REAR_TIRE_SQUAT = 0.0072                # 7.2 mm static load deflection
REAR_WHEEL_Z = REAR_TIRE_RAD - REAR_TIRE_SQUAT     # 0.348 m
REAR_TRACK = 1.676                      # Flush fitment inside 1987 mm haunches
REAR_WHEEL_X = REAR_TRACK * 0.5         # 0.838 m (outer tire face at 0.9855 m)

# Wheel arch openings (concentric to wheels)
FRONT_ARCH_RAD = 0.398                  # ~38.5 mm radial clearance
REAR_ARCH_RAD = 0.395                   # ~39.8 mm radial clearance

# Brakes (2023-2024 Plaid Red Calipers)
FRONT_ROTOR_RAD = 0.190                 # 380 mm diameter
FRONT_ROTOR_THICK = 0.034               # 34 mm ventilated
REAR_ROTOR_RAD = 0.1825                 # 365 mm diameter
REAR_ROTOR_THICK = 0.028                # 28 mm ventilated

# Panel shutline gap parameters
PANEL_GAP = 0.0035                      # 3.5 mm crisp automotive panel gap
PANEL_FLANGE_DEPTH = 0.014              # 14 mm inward rolled return flange
PANEL_BEVEL_RAD = 0.0022                # 2.2 mm rolled panel edge catch-light

# Key Longitudinal Y stations for structural consistency across modules
Y_HOOD_FRONT = 2.385
Y_COWL_CENTER = 0.955
Y_COWL_SIDE = 0.870
Y_ROOF_FRONT = 0.110
Y_ROOF_PEAK = -0.180
Y_B_PILLAR = -0.220
Y_ROOF_REAR = -1.100
Y_HATCH_GLASS_BOT = -2.140
Y_DECKLID_TIP = -2.475
Y_REAR_BUMPER_TOP = -2.535

# Door shutline X/Y reference stations
Y_FENDER_DOOR_TOP = 0.885
Y_FENDER_DOOR_BOT = 0.945
Y_FRONT_REAR_DOOR_TOP = -0.220
Y_FRONT_REAR_DOOR_BOT = -0.195
Y_REAR_DOOR_TOP = -1.030

# Ultra Red (PR01) physical color targets (Linear sRGB - calibrated against real PR01 studio photos)
ULTRA_RED_DIRECT = (0.30, 0.0022, 0.0042, 1.0)    # Saturated glowing crimson under direct light
ULTRA_RED_MID = (0.095, 0.0007, 0.0018, 1.0)      # Deep sumptuous cherry-ruby midtone
ULTRA_RED_FLOP = (0.014, 0.00015, 0.0006, 1.0)    # Ultra-deep dark wine-burgundy grazing flop
