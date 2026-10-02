# Avoid Windows-reserved default HTTP port 8011. Installation stays unchanged.
$isaacLauncher = 'C:/isaacsim/isaac-sim.bat'
if (-not (Test-Path -LiteralPath $isaacLauncher)) { throw "Isaac Sim launcher missing: $isaacLauncher" }
& $isaacLauncher '--/exts/omni.services.transport.server.http/port=18011' '--/exts/omni.services.transport.server.http/allow_port_range=false' @args
