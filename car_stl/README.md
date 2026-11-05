# Wrapped STL to CAD

Source: `car_wrapped.stl`, a closed surface-wrap mesh (44,802 triangles, mm; X = length, nose at −X; Y = width; Z = up).

## Stage 1: wheels, floor, wheel regions (`stage1_wheels_floor.step`)

| Part | Measured from the mesh |
|---|---|
| Front wheels | centre x −1339, z 387; r 386.4; \|y\| 630–990 (both sides agree within ~2 mm) |
| Rear wheels | centre x +1351, z 398; r 397.1; \|y\| 630–1009 |
| Floor | plane z = 101.0 + 0.00174·x (0.1° rake); 90 % of floor points within 4 mm |
| Wheel regions | cut volumes: well cylinder (tyre + 12 mm front / + 8 mm rear) plus the open space below the axle, from the slot wall (\|y\| 558 front / 545 rear) outwards |

The fender top is only 24 mm (front) and 13 mm (rear) above the tyres in the mesh, which limits the well clearance.

`tools/` holds the analysis and build scripts; `renders/` holds the analysis and check images.
