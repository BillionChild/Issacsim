# Pickup anomaly capture implementation plan

Goal: approved stage one only: separate RGB-D test scene with four independent conditions.
Spec: ../specs/2026-10-11-pickup-anomaly-design.md
Implementation is inline, following the user's instruction to proceed.

- Build a referenced test stage, shared engine/pallet transform, top-down calibrated camera.
- Add deterministic X/Y/yaw/observation-mask presets and combined presets.
- Add an editor panel and asynchronous RGB/depth export with isolated ground-truth metadata.
- Verify transforms, resets, camera output and source preservation; inspect an exported image.
- Document loading, limitations and remaining perception/control stages.

No changes to warehouse scheduler or production dimensions. Offsets are small test inputs,
not validated robot correction limits. No robot execution in this observation-only stage.
