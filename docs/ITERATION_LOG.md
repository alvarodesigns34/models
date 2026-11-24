# Iteration & Visual QA Log — Tesla Model S Plaid (Ultra Red)

This document tracks every **INVESTIGATE → MODEL → RENDER → INSPECT → COMPARE → IDENTIFY DEFECTS → FIX → VALIDATE → REPEAT** cycle against authentic photographic references of the **2024 Tesla Model S Plaid (`PR01` Ultra Red)**.

---

## Iteration 0 — Environment, Tooling & Research Setup
- **Toolchain**: Installed official **Blender 4.2.23 LTS** (Cycles CPU + OpenImageDenoise + AgX OpenColorIO + NumPy 1.24.3) and **Git LFS 3.4.1**.
- **Reference Acquisition**: Collected official millimeter dimensions from Tesla Model S Owner's Manual (`5021 × 1987 × 1430 mm`, `2960 mm` wheelbase, `2189 mm` width with mirrors) and high-resolution photographs of 2023–2024 Model S Plaid exteriors (`references/wikimedia/`), Ultra Red (`PR01`) multi-angle flop references, 21" Arachnid wheels, Matrix LED headlights, 2022+ refreshed taillights, rear Plaid warp badge, and 2024 Sport Seats.
- **Version Lock**: Locked **2024 Tesla Model S Plaid Ultra Red (MY2024 post-April 2024 Fremont build, HW4/AI4)** for 100% component coherence.

---

## Iteration 1 — Initial Full-Vehicle Parametric Build & First Visual Audit
- **Build Stats**: 224 objects, 113,128 vertices, 14 procedural/PIL PBR textures generated in `textures/`.
- **Renders Evaluated**: `renders/iterations/iter01/studio_{front_3q,rear_3q,side_left}.png` (960×540 @ 32 spp, Cycles + OIDN + AgX).
- **Defects Identified (Classified by Realism Impact)**:
  - **[P0 - Critical]** `Body_Front_Fender` and `Body_Rear_Quarter` rendered pitch black due to inverted polar quad normals (`flip_normals=True`).
  - **[P0 - Critical]** `Env_Studio_Cyclorama` had inverted normals (floor overexposed white, cyclorama wall void black) and side area lights (`950–1150 W` at `Z = 1.55 m`) washed the doors flat salmon-pink.
  - **[P0 - Critical]** Double-walled `Solidify` + `Principled Transmission` glass caused milky frosted total-internal-reflection fog, hiding the interior cabin and slowing Cycles rendering ~2.5×.
  - **[P1 - High]** Camera presets cropped nose and rear overhang in `front_3q` / `rear_3q`.
  - **[P1 - High]** 21" Arachnid wheel spokes were too narrow compared to authentic OEM wide chiseled blades (`IMG_9278.jpg`).
  - **[P1 - High]** Side mirror shells had open rear ends; Michelin sidewall checkered velvet arcs overlapped text.

---

## Iteration 2 — Core Normal, Glass, Lighting, Camera & Arachnid Spoke Overhaul
- **Fixes Applied**:
  - Corrected outward normals (`flip_normals=False`) on `Body_Front_Fender`, `Body_Rear_Quarter`, and `Env_Studio_Cyclorama`.
  - Replaced double-walled `Solidify` glass with physically accurate single-sheet Fresnel architectural glass (`Transparent + Glossy` + `Is Shadow Ray` pass-through) — crystal-clear reflections, visible 2024 Sport Seats & Yoke, ~2× faster Cycles tracing.
  - Elevated studio side sculpting strips (`Z = 2.85 m`, reduced intensity) and calibrated Ultra Red `PR01` 3-angle Fresnel flop + metallic Voronoi flake sparkle.
  - Rebuilt 21" Arachnid spokes with wider flat-chiseled trapezoidal blades, made side mirrors watertight, fixed Michelin sidewall texture layout, and pulled back all camera presets for full-vehicle commercial framing.
- **Build Audit**: 226 objects, 107,732 vertices — Length `5010.7 mm`, Body Width `1989.3 mm`, Mirror Width `2189.0 mm`, Height `1428.4 mm`, Ground Z `+0.5 mm`.
- **Renders Evaluated**: All 5 views (`front_3q`, `rear_3q`, `side_left`, `front_pure`, `rear_pure`) in `renders/iterations/iter02/` (800×450 @ 28 spp) inspected directly against Wikimedia reference photos.
- **Defects Identified in Iteration 2**:
  - **[P0 - Critical]** Rear triangular gap/hole directly under outer taillight + diagonal rear bumper pinch where `Body_Rear_Quarter` terminated before wrapping to the tailgate shutline.
  - **[P0 - Critical]** Rear bumper red crescents poking through the gloss-black trapezoidal rear diffuser valence.
  - **[P0 - Critical]** Front bumper ↔ front fender vertical seam slit (`Body_Front_Bumper` did not wrap onto lower front wheel arch edge to meet `Body_Front_Fender` at the authentic `phi = 28°` seam).
  - **[P1 - High]** Raised roof cantrail "horns" visible at top-left/top-right roofline in `front_pure` and `rear_pure`.
  - **[P1 - High]** Left tire sidewalls still rendered medium-grey due to inverted `side_sign > 0` winding check in `wheels_brakes.py:build_sw_mesh`.
  - **[P1 - High]** Rear Plaid warp badge (`Emblem_Rear_Plaid_Badge`) sat 30 mm inside the tailgate curvature and was invisible; rear `T E S L A` letters were too small/dark; rear taillights protruded slightly past rear quarter flank.
  - **[P1 - High]** Front Matrix LED headlight vertical aperture too narrow (~70 mm vs real ~104 mm) and front lower side intakes looked too boxy compared to `1X7A0025.jpg`.
  - **[P2 - Medium]** Wheel well liner edge visible slightly behind rear bumper; studio cyclorama wall pure black; harsh white rectangular softbox reflection in `front_pure` windshield.

---

## Iteration 3 — Factory Panel Topology, Flush Seam Engineering & Optical/Trim Alignment
- **Fixes Applied**:
  - **Exact OEM Panel Topology (`body_master.py`)**:
    - Rebuilt `Body_Front_Bumper` to form the lower-front wheel arch edge (`phi = -22°..+28°`) meeting `Body_Front_Fender` cleanly along the authentic short headlight-to-arch seam (`0.0 mm` gap). Sleeker lower nose (`Z_hood_front = 0.596 m`) + authentic horizontal needle-wedge fog recess and narrow outer air-curtain slit.
    - Added continuous `Body_Rear_Quarter_CornerWrap` connecting `Body_Rear_Quarter` (`phi = 150°`), `Body_Rear_Tailgate` (`0.646, -2.391, 0.960` down to `0.635, -2.452, 0.585`), and `Body_Rear_Bumper` along shared `eval_rear_bumper_top_seam(u)` (`0.0 mm` seam mismatch, eliminating rear hole & pinch).
    - Deeply recessed `Body_Rear_Bumper` behind `Trim_Rear_Diffuser` to eliminate red bleed-through.
    - Flattened `Body_Roof_Cantrail` crown (`4 mm`, flush `-1 mm` to glass) eliminating roof horns; dynamically tucked wheel liners `-18 mm` inside fenders.
  - **Lighting & Exterior Details (`lighting.py`, `exterior_details.py`, `materials.py`)**:
    - Aligned Matrix LED headlights to Iter 3 nose (`104 mm` vertical aperture + US-spec outer amber side-marker reflector) and dynamically locked 2-piece taillights onto `BodyCurves.eval_flank_x_at_yz` for flush rear-corner integration.
    - Centered chrome front `T` inside Iter 3 gloss-black mustache V-notch; moved `Emblem_Rear_Plaid_Badge` onto exact outer painted tailgate surface `_eval_tailgate_y(x, z)`; enlarged rear 3D `T E S L A` letters (`29 mm`, brighter dark-satin chrome); synchronized carbon spoiler trailing curve.
  - **Wheels, Tires & Brakes (`wheels_brakes.py`)**:
    - Fixed left/right tire sidewall outward normal winding (`side_sign < 0`) so both sides render deep vulcanized Michelin carbon-black with crisp raised sidewall bump lettering.
    - Added raised metallic `T` crest on all 4 Arachnid center caps and curved white `TESLA` decal plates on all 4 red Plaid brake calipers.
  - **Studio Environment (`environments.py`)**:
    - Added soft cyclorama wall wash lights for seamless dark slate studio backdrop gradient and elevated/softened overhead softbox ribbon.
- **Build Audit**: 236 objects, 110,444 vertices, 103,786 polygons — Length `5013.0 mm`, Body Width `1985.4 mm`, Mirror Width `2189.0 mm`, Height `1428.4 mm`, Ground Z `+0.5 mm`, zero build warnings.
- **Status**: Rendering 5-angle validation suite (`renders/iterations/iter03/`).
