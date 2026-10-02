# Context efficiency and engine optimization review (2026-10-02)

## Applied
- Root AGENTS.md condenses the supplied instructions into a short project-specific policy: partial reads, USD API summaries, bounded logs, reuse of findings and targeted verification.
- tools/inspect_usd.py provides bounded, read-only asset/subtree counts, bounds, material groups and the five largest meshes. Run with C:/isaacsim/kit/python/python.exe; use --out for a local JSON report.
- Existing tools/token_usage_report.py remains the native per-turn usage report. No duplicate accounting system was added. File size/read audits are not token measurements.
- AGENTS.md is repository guidance, not a technical output limiter or guaranteed cache policy. Work from this repository; a chat rooted elsewhere should explicitly read this file before repository work.

## Measured original asset
Source: external_assets/engines/caterham_duratec/usd/engine.usdc (unchanged).
14,112,058 bytes; 1,034 active composed prims; 979 meshes; 447,025 points; 339,936 triangular faces; 12 bound material groups.
World bounds size: approximately 0.604685 x 0.431245 x 0.479228 m.
No rigid-body/collision schemas in this visual asset. This is an inventory, not an FPS diagnosis.
Full local summary: outputs/engine-mesh-inventory.json.

## Proposed optimization order (not yet applied)
1. Separate candidate USD, same scale/origin/materials. Merge compatible static meshes by material, keeping future vision-inspection parts individually identifiable. Twelve materials do not guarantee twelve output meshes: primvars, transforms and semantics constrain merging. Preserve UVs, normals, double-sided settings and texture paths.
2. Compare original/candidate in the same camera, resolution, renderer and playback section after warmup. Record app-update FPS and runtime CPU time with the existing CSV exporter; use GPU profiling if those do not locate the bottleneck. Mesh count is not an exact draw-call count.
3. If needed, try moderate decimation (initial candidate: retain about 50% of faces). This is an experiment, not an accepted target. Protect silhouettes, locating/gripping surfaces and inspection features. Check bounds, close-up appearance, UV seams and references before adoption.
4. Optional distant-view LOD/proxy for layout work. It must not replace the detailed inspection model or stand in for validated collision geometry.

Polygon reduction primarily concerns rendering/geometry workload. Locally processing a mesh does not insert its vertices into model context; printing the mesh or large logs does. No cache price ratio, model-price claim, guaranteed token reduction or FPS gain is inferred from this review.

Sources:
- https://learn.chatgpt.com/docs/agent-configuration/agents-md
- https://docs.omniverse.nvidia.com/extensions/latest/ext_scene-optimizer/howto.html
- https://docs.omniverse.nvidia.com/extensions/latest/ext_scene-optimizer/operations.html

## This task's context audit
- Supplied text/skill guidance: full small-document reads; the first combined output was too broad and truncated. Follow-up read covered only the missing attachment tail. Future reads are bounded by the new policy.
- convert_engine.py: first 65 lines only, to confirm asset/material handling.
- engine.usdc: metadata plus API scan; no raw vertices/indices or full USD text entered chat. No engine source edits.
- No Isaac startup log or whole repository contents read. No editor restart or GPU benchmark performed.
- Likely context contributors: supplied conversation/guidance and web documentation output; geometry arrays contributed none. These are qualitative observations, not per-file billed tokens.

## Material merge candidate (2026-10-02)
Implemented `merge_engine_meshes.py`, a scoped offline USD merger for the flat static output of our converter. This follows the material-preserving merge approach in NVIDIA's guidance; it does not invoke NVIDIA Scene Optimizer itself. Unexpected animated/transformed/subset geometry or unsupported authored properties abort rather than silently losing data.

- Original 979 meshes -> 12 compatible material groups; all 339,936 triangles retained.
- Exact per-source verification after reopening: points, face counts/indices/winding, normals, UVs and material bindings. Material values/connections, resolved textures, stage units/up axis and world bounds checked; source SHA256 unchanged.
- Original 14,112,058 bytes; candidate 18,046,921 bytes. A fresh crate export avoids stale removed geometry blocks; grouping still changes binary packing/deduplication. This is not a file-size reduction.
- Candidate: external_assets/engines/caterham_duratec/usd/engine_merged.usdc.
- Open engine_merged_preview.usda in that folder to inspect the merged engine on the existing support fixture. Current warehouse references remain unchanged.
- outputs/engine-merge-report.json maps every original mesh to its output point/face ranges. This preserves traceability, not individual-part editability. Keep the original for future per-part vision labels or independently moving components.
- No rendered visual comparison or same-scene FPS comparison performed yet. Do not adopt as the warehouse default until these pass. No polygon decimation, collision modification or grip/support changes.

Guides:
- https://docs.isaacsim.omniverse.nvidia.com/latest/reference_material/sim_performance_optimization_handbook.html (Robot Asset Optimizations; Scene and Rendering Optimizations)
- https://docs.omniverse.nvidia.com/extensions/latest/ext_scene-optimizer/operations.html#merge-static-meshes

This task's audit: converter read only relevant mesh-writing section; original binary processed locally via USD/NumPy without printing arrays; bounded summary only. No Isaac restart or startup-log dump.
