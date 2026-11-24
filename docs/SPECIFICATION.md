# Technical Specification — 2024 Tesla Model S Plaid (Ultra Red)

## 1. Locked Target Configuration
To maintain 100% physical, optical, and trim coherence across every component, this project targets one exact production specification:

- **Vehicle**: 2024 Tesla Model S Plaid (MY2024, Fremont Factory, post-April 2024 build, HW4 / AI4)
- **Exterior Paint**: **Ultra Red Metallic (`PR01`)** — multi-layer crimson/ruby metallic basecoat with deep burgundy angular flop, micro metallic flake, and high-gloss automotive clearcoat
- **Exterior Trim**: OEM Blackout / Chrome-Delete (satin black DLO window moldings, satin black flush door handles, gloss black B-pillar camera glass, satin black HW4 side repeater housings, body-color mirror upper cap + satin black lower arm/sail, gloss black rear tailgate bar with spaced dark-satin `T E S L A` letters, metallic geometric Plaid warp emblem on right lower tailgate, satin 2x2 twill carbon fiber rear decklid lip spoiler, satin/gloss black lower rear diffuser with integrated red reflectors)
- **Wheels & Tires (Staggered 21" Arachnid Setup)**:
  - **Front**: `21 × 9.5J ET40` Satin Dark Anthracite Arachnid 10-spoke (5 twin-V split pairs) + `265/35 ZR21` Michelin Pilot Sport 4S (unloaded OD `718.9 mm`, section width `265 mm`)
  - **Rear**: `21 × 10.5J ET45` Satin Dark Anthracite Arachnid 10-spoke (deeper concave dish) + `295/30 ZR21` Michelin Pilot Sport 4S (unloaded OD `710.4 mm`, section width `295 mm`)
  - **Bolt Pattern**: `5 × 120 mm`, center bore `64.1 mm`
- **Brake System (2023–2024 Plaid Upgraded Red Calipers)**:
  - **Front**: `380 × 34 mm` ventilated cast-iron rotors, rear-mounted gloss red 4-piston monoblock calipers with white `TESLA` script
  - **Rear**: `365 × 28 mm` ventilated cast-iron rotors, front-mounted gloss red main calipers + auxiliary rear-upper electronic parking brake (EPB) caliper
- **Lighting (2022–2024 Refreshed Optics)**:
  - **Front**: Adaptive Matrix LED headlamps (outer Bi-LED projector dome, inner multi-chamber chrome LED array, continuous white LED DRL boomerang, dark housing) + recessed lower horizontal LED fog/accent strips in side air-curtain intakes
  - **Rear**: 2022+ refreshed 2-piece split LED taillights (bold crimson U/C light-pipe loop, twin dark smoked horizontal inner bars, lower clear LED reverse strip, black housing, flush tailgate garnish that terminates cleanly at inner lamp edge)
- **Interior (2024 Plaid All-Black Premium Interior + Carbon Fiber Décor + Sport Seats)**:
  - **Seats**: 2024 Plaid Sport Seats — deeply bolstered perforated black vegan leather, charcoal Alcantara/suede bolster inserts, integrated tapered headrest, recessed upper-backrest Plaid composite emblem
  - **Controls & Displays**: Steering Yoke (flat-top leather/satin-silver rim, scroll wheels, haptic controls, silver `T` airbag pad), `12.3"` recessed driver instrument cluster, `17.0"` landscape floating central touchscreen, `9.4"` rear console touchscreen
  - **Trim**: Full-width matte 2x2 twill carbon fiber dash, door-panel inlays, and center console sliding covers; panoramic all-glass roof; black Alcantara headliner and pillars

## 2. Official Dimensional Control Table (1:1 Metric, Blender Units = Meters)

Coordinate System:
- `+X`: Right (Passenger side, LHD) / `-X`: Left (Driver side, LHD)
- `+Y`: Forward (Front nose) / `-Y`: Rearward (Rear bumper)
- `+Z`: Up / `Z = 0.000 m`: Ground plane

| Parameter | Official Spec | Blender Model Target |
|---|---|---|
| Overall Length | 5,021 mm (197.7 in) | `5.021 m` (`Y = -2.580` to `+2.441`) |
| Wheelbase | 2,960 mm (116.5 in) | `2.960 m` (`Y_front = +1.480`, `Y_rear = -1.480`) |
| Front Overhang | 961 mm (37.8 in) | `0.961 m` (`+1.480` to `+2.441`) |
| Rear Overhang | 1,100 mm (43.3 in) | `1.100 m` (`-1.480` to `-2.580`) |
| Overall Width (excl. mirrors) | 1,987 mm (78.2 in) | `1.987 m` (`X = ±0.9935` at rear haunches) |
| Overall Width (incl. mirrors) | 2,189 mm (86.2 in) | `2.189 m` (`X = ±1.0945` at mirror tips) |
| Overall Height (Low/Medium stance) | 1,430–1,431 mm (56.3 in) | `1.430 m` (roof crown peak at `Y ≈ +0.05`) |
| Ground Clearance (Sport Low) | 117–126 mm | `0.122 m` (under flat battery tray/sills) |
| Front Track (wheel center) | 1,690 mm (66.5 in) | `1.690 m` (`X = ±0.845 m`) |
| Rear Track (wheel center) | 1,676–1,700 mm | `1.676 m` (`X = ±0.838 m`, flush 295 mm sidewall) |
| Front Tire OD (`265/35 ZR21`) | 718.9 mm (`R = 359.5 mm`) | Loaded hub `Z = 0.352 m` (7.5 mm static squat) |
| Rear Tire OD (`295/30 ZR21`) | 710.4 mm (`R = 355.2 mm`) | Loaded hub `Z = 0.348 m` (7.2 mm static squat) |

## 3. Primary Photographic References
- Wikimedia Commons CC-licensed high-resolution 2023–2024 Model S Plaid photographs in `references/wikimedia/` (front 3/4, rear 3/4, front close-up, side 3/4, Arachnid wheels, Matrix headlights, 2022+ taillights, Plaid badge, rear diffuser).
- Official Tesla Model S Owner's Manual dimensional specifications (`tesla.com/ownersmanual/models/en_us/`).
- Official Tesla Ultra Red (`PR01`) vs Red Multi-Coat (`PPMR`) studio & outdoor photographic comparisons.
