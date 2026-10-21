# Smoothness pass: plan

Goal: prettier and smoother, with no new details. The side view must keep matching the sketch.

1. [x] Honest preview: finer mesh and smooth shading in the renderer. Geometry untouched.
2. [x] Fuller sections: bigger shoulder radius, sides lean inward toward the bottom, softer bottom corner.
3. [x] Canopy blend: dome meets the deck tangentially (no crease at its base), with a round crown.
4. [ ] Rounded ends: not achieved. Shrinking end sections and cap-edge fillets (6–50 mm) all produce an invalid solid on this surface, so the ends stay flat.
5. [x] Soften cut edges: done where the kernel allows. 14 of 58 cut edges are filleted one at a time; the rest stay sharp because the fillet fails on them.: arch lips 12 mm; scoop, sill, intake and rear-recess openings 6–8 mm.
6. [x] Verify and deliver (STEP re-imports with 9 valid solids; side view still on the sketch; renders/before_after.png): overlay on sketch, STEP round-trip, before/after renders.
