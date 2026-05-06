$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$root = Split-Path -Parent $PSScriptRoot
$assets = Join-Path $root "assets"
$sounds = Join-Path $assets "sounds"
New-Item -ItemType Directory -Force -Path $assets, $sounds | Out-Null

function New-JarvisBitmap($size) {
  $bitmap = New-Object System.Drawing.Bitmap $size, $size
  $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
  $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $graphics.Clear([System.Drawing.Color]::FromArgb(2, 4, 10))

  $rect = New-Object System.Drawing.Rectangle 0, 0, $size, $size
  $bg = New-Object System.Drawing.Drawing2D.LinearGradientBrush $rect,
    ([System.Drawing.Color]::FromArgb(8, 18, 32)),
    ([System.Drawing.Color]::FromArgb(3, 6, 14)),
    45
  $graphics.FillRectangle($bg, $rect)

  $cyan = [System.Drawing.Color]::FromArgb(56, 246, 255)
  $violet = [System.Drawing.Color]::FromArgb(168, 85, 247)
  $white = [System.Drawing.Color]::FromArgb(235, 252, 255)
  $center = $size / 2

  for ($i = 0; $i -lt 5; $i++) {
    $radius = ($size * 0.18) + ($i * $size * 0.075)
    $alpha = 130 - ($i * 18)
    $pen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb($alpha, $cyan)), ([Math]::Max(1, $size / 140))
    $graphics.DrawEllipse($pen, $center - $radius, $center - $radius, $radius * 2, $radius * 2)
    $pen.Dispose()
  }

  $coreRadius = $size * 0.17
  $glowBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(52, $cyan))
  $graphics.FillEllipse($glowBrush, $center - ($coreRadius * 1.75), $center - ($coreRadius * 1.75), $coreRadius * 3.5, $coreRadius * 3.5)
  $coreBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(215, $cyan))
  $graphics.FillEllipse($coreBrush, $center - $coreRadius, $center - $coreRadius, $coreRadius * 2, $coreRadius * 2)
  $innerBrush = New-Object System.Drawing.SolidBrush $white
  $graphics.FillEllipse($innerBrush, $center - ($coreRadius * 0.48), $center - ($coreRadius * 0.48), $coreRadius * 0.96, $coreRadius * 0.96)

  $fontSize = [Math]::Max(16, $size / 5.2)
  $font = New-Object System.Drawing.Font "Segoe UI", $fontSize, ([System.Drawing.FontStyle]::Bold), ([System.Drawing.GraphicsUnit]::Pixel)
  $format = New-Object System.Drawing.StringFormat
  $format.Alignment = [System.Drawing.StringAlignment]::Center
  $format.LineAlignment = [System.Drawing.StringAlignment]::Center
  $textBrush = New-Object System.Drawing.SolidBrush $white
  $textRect = New-Object System.Drawing.RectangleF -ArgumentList 0, ($size * 0.63), $size, ($size * 0.24)
  $graphics.DrawString("JX", $font, $textBrush, $textRect, $format)

  $graphics.Dispose()
  return $bitmap
}

$png = New-JarvisBitmap 1024
$png.Save((Join-Path $assets "splash.png"), [System.Drawing.Imaging.ImageFormat]::Png)
$png.Dispose()

$icoBitmap = New-JarvisBitmap 256
$iconPath = Join-Path $assets "icon.ico"
$stream = New-Object System.IO.FileStream -ArgumentList $iconPath, ([System.IO.FileMode]::Create)
$icon = [System.Drawing.Icon]::FromHandle($icoBitmap.GetHicon())
$icon.Save($stream)
$stream.Close()
$icon.Dispose()
$icoBitmap.Dispose()

$wavPath = Join-Path $sounds "startup.wav"
$sampleRate = 44100
$duration = 0.8
$samples = [int]($sampleRate * $duration)
$memory = New-Object System.IO.MemoryStream
$writer = New-Object System.IO.BinaryWriter $memory
$writer.Write([Text.Encoding]::ASCII.GetBytes("RIFF"))
$writer.Write([int](36 + $samples * 2))
$writer.Write([Text.Encoding]::ASCII.GetBytes("WAVEfmt "))
$writer.Write([int]16)
$writer.Write([int16]1)
$writer.Write([int16]1)
$writer.Write([int]$sampleRate)
$writer.Write([int]($sampleRate * 2))
$writer.Write([int16]2)
$writer.Write([int16]16)
$writer.Write([Text.Encoding]::ASCII.GetBytes("data"))
$writer.Write([int]($samples * 2))
for ($i = 0; $i -lt $samples; $i++) {
  $t = $i / $sampleRate
  $freq = 220 + (660 * ($t / $duration))
  $amp = [Math]::Sin([Math]::PI * ($t / $duration)) * 0.35
  $value = [int16]([Math]::Sin(2 * [Math]::PI * $freq * $t) * 32767 * $amp)
  $writer.Write($value)
}
$writer.Flush()
[System.IO.File]::WriteAllBytes($wavPath, $memory.ToArray())
$writer.Dispose()
$memory.Dispose()
