# Concept car (STEP)

`concept_car.step` is a coloured AP214 assembly in mm. X runs rearward from the nose, Z is up from the ground and Y is lateral.
The parts are Body, Glazing, Headlamps and four plain cylinder wheels.

- Length is 4500 mm, the scale anchor. Width is 2094 mm and height is 1146 mm. Wheelbase is 2899 mm.
- The side elevation is driven straight by profiles traced from the concept sheet. `body.py` holds the keyframes in sheet pixels.
- `renders/overlay_on_sketch.png` shows the exported STEP drawn over the sheet: red is the silhouette, blue is the B-rep edges.

Rebuild:

    pip install cadquery-ocp==7.8.1.1 scipy pillow matplotlib
    python3 build_car.py && python3 export_step.py concept_car.step
    python3 overlay.py concept_car.step out/overlay.png   # check against the sheet
