# Franka manufacturing cell — baseline

## Run
Save and close any other Isaac Sim session first.

```powershell
cd C:\IssacsimProject\Issacsim
& C:\isaacsim\python.bat .\projects\franka-cell\pick_place.py --robot franka
```

After successful placement validation the simulation pauses and the window remains open until you close it. This is a one-cycle baseline; pressing Play does not restart the controller.
Tests (--test), headless runs (--headless), and errors keep the original exit behavior.

## Source
Adapted from Isaac Sim 6.1.0 installation:
standalone_examples/api/isaacsim.robot_motion.examples/manipulation/pick_place.py

NVIDIA's Apache-2.0 source header is preserved. See LICENSE for the license text.
Official tutorial: https://docs.isaacsim.omniverse.nvidia.com/6.1.0/core_api_tutorials/tutorial_core_adding_manipulator.html

## Execution mode
This script creates SimulationApp and is a standalone program, not Script Editor code.
An in-app version requires asynchronous app updates and a separate lifecycle; do not paste this entire file into Script Editor.

## Validation
The original example completed successfully in the user's reported run.
The modified exit control is checked separately; graphical operation of this project copy still needs user confirmation.
