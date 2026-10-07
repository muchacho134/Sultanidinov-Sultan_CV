P262 rail/handguard rebuild (OCP 7.8, `pip install "cadquery-ocp<7.9"`).

Inputs (relative to the working dir): `in/rail_completed.step` (= output/rail_completed.step, original open shell),
`work/p0NN.brep` parts dumped from output/Gun_solids_v6_grouped.step (17 Gas_Cylinder, 8 P213, 27 P223, 55 P214).

1. `build.py 0.012`  – right half (x >= 0.01): original faces + hole patches + inner-skin cavity prism + cut planes
                       -> BOPAlgo_MakerVolume, keep cells outside the cavity -> keep_cells.brep
2. `finish.py` / `ov2.py` – mirror about x = 0.01, fuse, unify; subtract the 0.13 mm3 sliver shared with P223
3. `export.py out.step "<name>"` – STEP AP214, global coordinates, product name kept
4. `final2.py out.step` – single solid / free edges / self-intersections / overlaps / clearances
`leaks.py`, `chunk.py` are the leak finders used while closing the holes.
