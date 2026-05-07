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

function New-ResizedBitmap($source, $size) {
  $bitmap = New-Object System.Drawing.Bitmap $size, $size, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
  $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
  $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
  $graphics.Clear([System.Drawing.Color]::Transparent)
  $graphics.DrawImage($source, 0, 0, $size, $size)
  $graphics.Dispose()
  return $bitmap
}

function Get-PngBytes($bitmap) {
  $memory = New-Object System.IO.MemoryStream
  $bitmap.Save($memory, [System.Drawing.Imaging.ImageFormat]::Png)
  $bytes = $memory.ToArray()
  $memory.Dispose()
  return ,$bytes
}

function Save-PngIcon($source, $iconPath) {
  $sizes = @(16, 24, 32, 48, 64, 128, 256)
  $images = @()
  foreach ($size in $sizes) {
    $resized = New-ResizedBitmap $source $size
    $images += ,(Get-PngBytes $resized)
    $resized.Dispose()
  }

  $stream = New-Object System.IO.FileStream -ArgumentList $iconPath, ([System.IO.FileMode]::Create), ([System.IO.FileAccess]::Write)
  $writer = New-Object System.IO.BinaryWriter $stream
  $writer.Write([UInt16]0)
  $writer.Write([UInt16]1)
  $writer.Write([UInt16]$sizes.Count)

  $offset = 6 + (16 * $sizes.Count)
  for ($i = 0; $i -lt $sizes.Count; $i++) {
    $size = $sizes[$i]
    $bytes = [byte[]]$images[$i]
    $writer.Write([byte]($(if ($size -ge 256) { 0 } else { $size })))
    $writer.Write([byte]($(if ($size -ge 256) { 0 } else { $size })))
    $writer.Write([byte]0)
    $writer.Write([byte]0)
    $writer.Write([UInt16]1)
    $writer.Write([UInt16]32)
    $writer.Write([UInt32]$bytes.Length)
    $writer.Write([UInt32]$offset)
    $offset += $bytes.Length
  }

  foreach ($bytes in $images) {
    $writer.Write([byte[]]$bytes)
  }
  $writer.Dispose()
  $stream.Dispose()
}

$logoSource = Join-Path $assets "logo.png"
if (Test-Path $logoSource) {
  $source = [System.Drawing.Bitmap]::FromFile($logoSource)

  $png = New-ResizedBitmap $source 1024
  $png.Save((Join-Path $assets "splash.png"), [System.Drawing.Imaging.ImageFormat]::Png)
  $png.Dispose()

  $iconPath = Join-Path $assets "icon.ico"
  Save-PngIcon $source $iconPath
  Copy-Item $iconPath (Join-Path $assets "jx-jarvis.ico") -Force
  $source.Dispose()
} else {
  $png = New-JarvisBitmap 1024
  $png.Save((Join-Path $assets "splash.png"), [System.Drawing.Imaging.ImageFormat]::Png)
  $png.Dispose()

  $icoBitmap = New-JarvisBitmap 256
  $iconPath = Join-Path $assets "icon.ico"
  Save-PngIcon $icoBitmap $iconPath
  Copy-Item $iconPath (Join-Path $assets "jx-jarvis.ico") -Force
  $icoBitmap.Dispose()
}

$startupMp3 = Join-Path $sounds "startup.mp3"
$wavPath = Join-Path $sounds "startup.wav"
if (-not (Test-Path $startupMp3) -and -not (Test-Path $wavPath)) {
  $sampleRate = 44100
  $duration = 1.45
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

  function Get-Envelope($t, $start, $attack, $release, $length) {
    if ($t -lt $start -or $t -gt ($start + $length)) { return 0.0 }
    $local = $t - $start
    if ($local -lt $attack) { return $local / $attack }
    if ($local -gt ($length - $release)) { return [Math]::Max(0.0, ($length - $local) / $release) }
    return 1.0
  }

  for ($i = 0; $i -lt $samples; $i++) {
    $t = $i / $sampleRate

    $master = [Math]::Sin([Math]::PI * ($t / $duration))
    $master = [Math]::Pow([Math]::Max(0.0, $master), 0.55)

    $bassEnv = Get-Envelope $t 0.00 0.035 0.45 0.90
    $bass = [Math]::Sin(2 * [Math]::PI * 110 * $t) * 0.18 * $bassEnv
    $bass += [Math]::Sin(2 * [Math]::PI * 220 * $t) * 0.06 * $bassEnv

    $sweepFreq = 420 + (980 * [Math]::Pow(($t / $duration), 1.35))
    $sweepEnv = Get-Envelope $t 0.08 0.08 0.38 1.05
    $sweep = [Math]::Sin(2 * [Math]::PI * $sweepFreq * $t) * 0.12 * $sweepEnv

    $pulse1 = [Math]::Sin(2 * [Math]::PI * 523.25 * $t) * 0.12 * (Get-Envelope $t 0.35 0.025 0.16 0.30)
    $pulse2 = [Math]::Sin(2 * [Math]::PI * 659.25 * $t) * 0.11 * (Get-Envelope $t 0.52 0.025 0.18 0.32)
    $pulse3 = [Math]::Sin(2 * [Math]::PI * 783.99 * $t) * 0.10 * (Get-Envelope $t 0.70 0.025 0.22 0.38)

    $readyEnv = Get-Envelope $t 1.02 0.035 0.26 0.42
    $ready = (
      [Math]::Sin(2 * [Math]::PI * 880.00 * $t) * 0.10 +
      [Math]::Sin(2 * [Math]::PI * 1108.73 * $t) * 0.08 +
      [Math]::Sin(2 * [Math]::PI * 1318.51 * $t) * 0.06
    ) * $readyEnv

    $signal = ($bass + $sweep + $pulse1 + $pulse2 + $pulse3 + $ready) * $master
    $signal = [Math]::Max(-0.85, [Math]::Min(0.85, $signal))
    $value = [int16]($signal * 32767)
    $writer.Write($value)
  }
  $writer.Flush()
  [System.IO.File]::WriteAllBytes($wavPath, $memory.ToArray())
  $writer.Dispose()
  $memory.Dispose()
}
