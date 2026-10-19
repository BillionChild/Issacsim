# Avoid Windows-reserved default HTTP port 8011. Installation stays unchanged.
$isaacLauncher = 'C:/isaacsim/isaac-sim.bat'
if (-not (Test-Path -LiteralPath $isaacLauncher)) { throw "Isaac Sim launcher missing: $isaacLauncher" }
$warehouseExtFolder = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../exts'))
if (-not (Test-Path -LiteralPath (Join-Path $warehouseExtFolder 'engine.warehouse/config/extension.toml'))) {
    throw "Engine Warehouse extension missing: $warehouseExtFolder"
}
& $isaacLauncher '--ext-folder' $warehouseExtFolder '--enable' 'engine.warehouse' '--/exts/omni.services.transport.server.http/port=18011' '--/exts/omni.services.transport.server.http/allow_port_range=false' @args
