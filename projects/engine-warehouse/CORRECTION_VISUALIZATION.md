# Correction explanation (first engine)

1. Reload the Engine Warehouse extension (OFF -> ON).
2. Load three-engine demo, select engine_combined, Apply case, Play.
3. After observation, the new Engine correction window opens. Pause to explain correction is enabled by default.
4. Green is the normal reference; orange is the accepted camera pose estimate. The frozen wrist image appears beside a schematic top/roll/pitch comparison. Diagram angles are exaggerated x5; translations are enlarged. Numeric values are actual estimates.
5. COMMANDED GRIP CHANGE is the difference between nominal and corrected attachment tool frames (world XYZ translation and world-relative Euler rotation), not the engine pose itself.
6. Continue corrected pickup resumes approach -> close/check -> lift at captured attitude -> level in air -> storage verification. Disable the explanation checkbox for uninterrupted playback. Correction view reopens the window.

The diagrams are UI-only and do not enter sensor captures. No injected anomaly values are read by this presentation layer. A rejected estimate does not draw a correction. Reset clears the display. VERIFIED requires an E1 seating check, not merely a controller state. This remains a kinematic grip demonstration; it does not establish force-contact validation.

Validation: three offline presentation tests; actual Kit camera/controller runs for engine_combined, normal, and occluded with retry all complete the three-engine sequence. Logs: logs/correction-ui-test.log; outputs/correction-ui-validation.json. Preview: outputs/correction-explanation-preview.png.
