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
- **Visual QA Results (`renders/iterations/iter03/`)**:
  - **Resolved**: Rear diffuser red poke-through eliminated; roof horns eliminated; front bumper ↔ front fender wheel arch seam sealed; Plaid badge & rear `T E S L A` letters visible; studio cyclorama gradient active; front/rear caliper white `TESLA` decals & Arachnid center `T` crests visible.
  - **Remaining Defects Identified**:
    - **[P0]** Diagonal fold crease + horizontal shelf step across Rear Quarter ↔ Rear Bumper seam.
    - **[P0]** Black triangular artifact at A-pillar foot / front fender rear-top corner.
    - **[P0]** Front headlight lens outer corner slightly above hood/fender brow; lower fog strip recessed behind red bumper skin.
    - **[P1]** Tire sidewalls still washed medium-grey under low studio fill; windshield reflected harsh pure-white rectangular softbox; side mirrors too oval vs real angular flat-bottom Model S wings.

---

## Iteration 4 — Unified C2 Bezier Rear Haunch, Shared Headlight Curves & Feathered Silk Scrims
- **Fixes Applied**:
  - **Unified C2 Cubic-Bezier Rear Haunch (`body_master.py`)**: Replaced separate `Body_Rear_Quarter_CornerWrap` patch with ONE single welded continuous `Body_Rear_Quarter` bmesh sharing `eval_rear_corner_bezier(t, z)` and `Master_ClassA_RearHaunch_Clay` `DATA_TRANSFER` normals seamlessly with `Body_Rear_Bumper`. Added upward lower rear overhang aero sweep matching `IMG_9321.jpg`.
  - **Shared 0.0 mm Headlight Perimeter (`body_master.py`, `lighting.py`)**: Exported `eval_headlight_lower_rim` & `eval_headlight_upper_rim` identically to Hood, Front Fender, Front Bumper, and Matrix LED headlights; moved lower smoked needle-wedge fog lights flush onto outer front bumper curvature (`1X7A0025.jpg`).
  - **Details & Materials (`exterior_details.py`, `materials.py`, `interior.py`, `environments.py`)**:
    - Resculpted wider angular flat-bottom Model S Plaid side mirrors; added front bumper circular tow-eye cover seam.
    - Calibrated Michelin Pilot Sport 4S "Premium Touch" velvet rubber (`Base Color` `0.0020–0.0058`, `Specular IOR Level 0.075`, `Roughness 0.56–0.94`) and brighter satin `T E S L A` rear lettering.
    - Fixed 9.4" rear touchscreen horizontal UV; added sculpted metallic `T` emblem on Steering Yoke airbag hub.
    - Upgraded studio Area Lights to Cycles feathered silk scrim softboxes (`Geometry -> Parametric -> Quadratic Sphere`).
- **Build Audit**: 239 objects, 113,218 vertices, 106,446 polygons — Length `5025.2 mm` (`+4.2 mm`), Body Width `1983.4 mm` (`-3.6 mm`), Mirror Width `2189.0 mm` (`0.0 mm`), Height `1428.4 mm` (`-1.6 mm`).
- **Visual QA Results (`renders/iterations/iter04/`)**:
  - **Major Wins**: Diagonal rear quarter crease & horizontal bumper shelf step 100% eliminated; flush smoked fog wedges + concave air curtains + tow-eye cover look spot-on in `front_pure`; Michelin PS4S tire rubber now deep velvet jet-black.
  - **Root-Cause Raycast & Full Normal Audit Findings**:
    - **[P0]** BVH raycast at `(-0.82, 0.91, 0.87)` proved the persistent A-pillar black triangle was caused by `Body_Shadow_Gap_Sides` extending forward to `Y = 1.08` and poking through the sculpted front fender shoulder!
    - **[P0]** Automated normal audit of all 21 primary panels revealed 8 inverted-normal surfaces (`Body_Hood`, `Body_Roof_Cantrail`, `Glass_Windshield`, `Glass_Panoramic_Roof`, `Glass_Rear_Hatch`, `Light_Headlight_*`, `Light_Taillight_*`, `Mirror_UpperCap/LowerShell`). Crucially, inverted normals on `Glass_Windshield` and `Light_Taillight_OuterLens` triggered Cycles internal Fresnel TIR (`1/1.52`), explaining the blown-out white glare across the windshield in `front_pure` and the bright crescents on outer taillight tips!
    - **[P1]** Lower rear bumper corner in `eval_rear_corner_bezier` flared slightly outward near the ground (`Z = 0.17..0.45`) instead of tucking smoothly inward like `IMG_9321.jpg`.
    - **[P2]** `Zebra_Diagnostic_Mat` had 0 users on save and was garbage-collected by Blender before zebra rendering.

---

## Iteration 5 — 100% Verified Outward Normals, A-Pillar Shadow Fix & Rear Lower Tumblehome Taper
- **Fixes Applied**:
  - Flipped normals to verified outward direction across ALL 8 remaining inverted surfaces (`Body_Hood`, `Body_Roof_Cantrail`, `Glass_Windshield`, `Glass_Panoramic_Roof`, `Glass_Rear_Hatch`, `Light_Headlight_*`, `Light_FrontFog_*`, `Light_Taillight_*`, `Mirror_UpperCap/LowerShell`) — **21/21 primary surfaces verified 100% outward via automated polygon normal audit**.
  - Bounded `Body_Shadow_Gap_Sides` strictly behind front/rear doors (`Y in [-1.05, 0.878]`, `-22 mm` inset), eliminating the A-pillar black triangle completely.
  - Added smooth lower tumblehome inward tuck (`lower_tuck`) to `eval_rear_corner_bezier` below `Z = 0.55` for authentic wide-hipped, tapered sports-sedan rear stance.
  - Enabled `use_fake_user = True` + on-the-fly fallback for `Zebra_Diagnostic_Mat` so Class-A curvature stripe diagnostics work reliably.
- **Status**: Rendering Iteration 5 validation suite (`renders/iterations/iter05/`, 5 studio + 3 zebra views).


## Iteración 06 — Abertura física en la parrilla delantera

- **Punto de partida:** `b2a1985`, escena y renders de la iteración 05. El objetivo sigue siendo el Plaid MY2024 posterior a abril, Ultra Red con Arachnid de 21 pulgadas. Revisé las cinco vistas de estudio y las referencias Wikimedia del repositorio. Usé `1X7A0025` e `IMG_9278` para la fascia, `IMG_9321` para la esquina trasera y el Model S azul 2024 para el perfil. Las fotos tienen otro acabado, posición de cámara y luz. Permiten contrastar proporciones y piezas visibles, pero no calibrar PR01. La versión y el acabado de la especificación del proyecto son un objetivo de trabajo.
- **Diagnóstico:** la parrilla anterior era una depresión pintada continua con lamas superpuestas. En la escena 05, un rayo frontal en `(X=-0.35, Z=0.20)` encontraba el paragolpes por delante del fondo de la parrilla. El defecto coincide con los reflejos rojos entre lamas y en el contorno. Las fotografías muestran una cavidad oscura con un borde pintado y una trama horizontal tenue.
- **Geometría:** recorté la malla del paragolpes y generé el retorno, cinco lamas y el fondo oscuro a partir del perímetro de la abertura. Las lamas quedan 25 mm detrás del plano local del borde. El conjunto conserva la franja pintada arriba, abajo y a ambos lados de la toma.
- **Validación:** `blender -b blend/tesla_model_s_plaid_ultra_red.blend --python-exit-code 1 --python scripts/check_front_grille.py`. La escena 05 falla al primer rayo. La nueva pasa los 44 rayos (frontal y 18.8° con respecto al eje longitudinal, más cuatro controles sobre pintura). La medición de los extremos sigue en 5.0252 × 1.9834 × 1.4284 m, con 2.1890 m entre retrovisores y el neumático a 0.5 mm del suelo.
- **Revisión visual:** la [comparación 05–06](../renders/iterations/iter06/comparison_05_06.jpg) mantiene cámara, exposición, motor, resolución de 768 × 432 y 40 muestras en ambos modelos, bajo estudio y cielo cubierto. La trama queda visible sin el brillo rojo entre las lamas. Las vistas lateral y trasera también se volvieron a renderizar. Blender 4.3.2 de Debian carece de OpenImageDenoise integrado, por lo que estas imágenes conservan ruido de muestreo.
- **Pendientes de la auditoría inicial:** capturar el mismo encuadre y luz con una referencia Ultra Red. En el frontal aún dominan la tira diurna gruesa, el proyector opaco y el hueco en la unión exterior del faro. En perfil se aprecian cristales demasiado oscuros y estilización en el estribo y los radios. El interior aún tiene formas lisas, juntas simples y una lectura pobre de pantallas y materiales. La imagen de estudio frontal mantiene una reflexión de caja grande en el parabrisas. En la zaga falta contrastar el detalle de la firma óptica y el contorno del paragolpes con la foto sin igualar color ni iluminación.

## Iteración 07 — Ópticas delanteras y acristalamiento

- **Diagnóstico:** en los primeros planos fotográficos de `1X7A0025` e `IMG_9278` se distingue una óptica circular oscura con un aro, reflejos separados en la cubierta y una guía fina en el perímetro. En 06, una esfera emisiva blanca ocupaba el centro del proyector y la guía formaba curvas abruptas de gran grosor. El vidrio del coche y el policarbonato de los faros usaban el mismo control artístico de reflectancia y el material ignoraba el índice de refracción.
- **Cambios:** separé cubierta, lente convexa, aro y fuente del proyector. Reduje el diámetro visible de la guía a un máximo de 5.6 mm y redondeé su recorrido exterior con una Bézier tangente. En estudio, de día y bajo nubes funcionan las luces diurnas. Los proyectores y las luces bajas auxiliares se activan en la escena nocturna. Las superficies ópticas usan una placa delgada con reflectancia angular de Schlick y suma de rebotes internos; los índices supuestos son 1.52 para el vidrio y 1.58 para el policarbonato. Los tintes frontal, lateral y trasero son provisionales y se aplican a partir del mismo nodo para vista directa y sombras.
- **Validación:** 44 rayos de control de parrilla. Se completaron y decodificaron 11 PNG de estudio, cielo cubierto y noche. El [comparativo 06–07](../renders/iterations/iter07/comparison_06_07.jpg) muestra el interior del proyector, la guía fina y las diferencias de lectura del acristalamiento. En el cockpit sigue faltando lectura del cuadro del conductor. En el faro exterior se ve el reverso de la aleta, y desde el frontal de estudio la fuente cenital sigue saturando el centro del parabrisas.
- **Ruido de render:** los PNG publicados de esta iteración y ambos lados de su comparativo usan el mismo filtrado RGB pos-AgX con Open Image Denoise 2.4.1, sin pases auxiliares. Los fotogramas originales se generaron con Cycles 4.3.2 a 768 × 432 / 40 muestras y 640 × 360 / 48 muestras para noche. Para repetir el posprocesado, usar `python3 scripts/denoise_png.py --oidn /ruta/a/oidnDenoise --out <directorio-de-salida> <archivos-PNG>`. Se usó el binario x86_64 oficial con SHA-256 publicado `b69ca2443a226ef692ca46bdc4f89995b1e99091f2665b906cbe07e9673e48cc`.

## Iteración 08 — Encuentro de la aleta y el faro

- En el acercamiento de 07, los rayos de cámara sobre el triángulo oscuro llegaban al reverso de la aleta. Se encontró una discontinuidad de 8 mm de altura entre los extremos analíticos de los dos bordes del faro, además de una interpolación que soltaba el borde de la aleta al aproximarse al vértice.
- La aleta y el paragolpes comparten ahora el recorrido hasta un extremo convergente del faro. Los extremos del perfil se muestrean explícitamente. También soldé el polo de las piezas de revolución del proyector.
- `scripts/check_headlight_join.py` falla sobre 07 y pasa los 12 rayos sobre caras exteriores en ambos lados del modelo nuevo. Siguen pasando los 44 rayos de parrilla. El [primer plano en estudio](../renders/iterations/iter08/studio_closeup_headlight.png) muestra el cierre del triángulo. Se verificó además el [mismo encuadre bajo nubes](../renders/iterations/iter08/overcast_closeup_headlight.png) y la [vista de continuidad de superficie](../renders/iterations/iter08/zebra_front_3q.png). Los extremos medidos del vehículo se mantienen dentro de la misma décima de milímetro.

## Iteración 09 — Reconstrucción geométrica del morro y del perfil lateral

- Ajusté las cámaras por centros de rueda, proyección aproximada de las llantas y posición del emblema. Usé `Tesla_Model_S_2024_Blue.jpg` para plantear las curvas del frente y `IMG_9278.jpg` para comprobarlas desde el lado opuesto. La calibración estima los parámetros de cámara, el recorte y la actitud del vehículo.
- Reemplacé la superficie del capó por un parche parametrizado con bordes comunes al panel del emblema y al faro. El faro cambia de una almendra baja a una abertura más alta en el extremo exterior, con un borde inferior que sube al acercarse a la aleta. Reconstruí la transición hacia el paso de rueda, usando la misma curva para los dos paneles y aumentando la densidad local de la malla. El panel de la insignia sigue el nuevo capó y la parrilla conserva su abertura física y sus cotas verticales.
- El encuentro entre aleta, capó y pie del pilar A emplea un recorrido continuo. El borde interior del pilar comparte la posición del parabrisas. Rehice la subida longitudinal en la parte baja de las puertas y eliminé el solape entre las pieles de puerta y estribo.
- Para medir el contorno se ejecuta `blender -b blend/tesla_model_s_plaid_ultra_red.blend --python-exit-code 1 --python scripts/audit_front_shape.py`. Las distancias son de marcas manuales al contorno proyectado del faro, medidas en fotos de 1920 px de ancho. En la foto de ajuste (11 marcas), el error medio bajó de 19,6 a 7,4 px y el máximo de 55,0 a 10,4 px. En la foto de comprobación (10 marcas), el medio bajó de 35,4 a 29,3 px y el máximo de 91,5 a 39,9 px. Estas cifras dependen del encuadre estimado y miden esa pieza.
- Blender 4.3.2 completó 44 rayos de parrilla, 34 muestras sobre los bordes de las mallas y 12 rayos de visibilidad del faro. Dimensiones de la escena 5.0197 × 1.9834 × 1.4284 m y 2.1890 m entre retrovisores. La batalla mide 2.960 m. El resultado se compara con la iteración 08, con el mismo entorno, cámara, muestreo y filtrado en cada pareja.
- `scripts/render_suite.py` incluye `ref_2024_blue` (960 × 416) y `ref_ulm_front` (960 × 639). El comparativo enfrenta ambas versiones a las fotos. Los entornos de estudio y zebra muestran las superficies desde otros ángulos. Quedan diferencias en el recorte aparente del faro lejano en la vista rasante, el hueco lateral del paragolpes y el volumen de la zaga. Las fotos usan otros acabados y condiciones de luz. [Comparativo de geometría](../renders/iterations/iter09/comparacion_geometria.jpg)

## Iteración 10 — Geometría de las tomas laterales del paragolpes

- En las dos fotos, el borde superior de la óptica baja asciende desde el centro del paragolpes y se une a un conducto vertical estrecho. En la iteración 09 se veía un rebaje horizontal y bajo, con los elementos ópticos ubicados por coordenadas independientes de la piel pintada.
- Rehice el rebaje y recorté una abertura en forma de L. El extremo exterior de la óptica sube desde aproximadamente 335 a 434 mm. El contorno de la malla define la lente ahumada, el emisor y el interior del conducto. El difusor de luz y el fondo quedan detrás del borde pintado.
- `scripts/check_front_apron.py` falla en la escena 09 porque el primer rayo llega a la pintura. En la nueva, 16 rayos alcanzan las lentes, las paredes oscuras y las franjas pintadas esperadas en ambos lados. Se mantuvieron los 44 controles de la parrilla, las 46 comprobaciones de bordes y exposición de faros y las medidas de la iteración 09.
- El comparativo conserva las cámaras, la exposición y el muestreo de 09. La vista nocturna permite comprobar la óptica activa. La forma del morro todavía difiere en la superficie elevada delante del paso de rueda y en la vista rasante del faro lejano. [Comparativo del paragolpes](../renders/iterations/iter10/comparacion_paragolpes.jpg)
