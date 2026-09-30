$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$outDir = Join-Path $PSScriptRoot '../Production/v001/textures'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$bmp = [Drawing.Bitmap]::new(1800,160)
$g = [Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = 'AntiAlias'
$g.TextRenderingHint = 'AntiAliasGridFit'
$g.Clear([Drawing.Color]::FromArgb(46,61,64))
$white = [Drawing.SolidBrush]::new([Drawing.Color]::FromArgb(237,237,216))
$yellow = [Drawing.SolidBrush]::new([Drawing.Color]::FromArgb(237,195,57))
$green = [Drawing.SolidBrush]::new([Drawing.Color]::FromArgb(34,145,96))
$blue = [Drawing.SolidBrush]::new([Drawing.Color]::FromArgb(40,137,191))
$big = [Drawing.Font]::new('Malgun Gothic',53,[Drawing.FontStyle]::Bold)
$small = [Drawing.Font]::new('Malgun Gothic',22)
$mid = [Drawing.Font]::new('Malgun Gothic',30,[Drawing.FontStyle]::Bold)
$g.FillEllipse($green,40,20,120,120)
$g.FillEllipse($blue,180,20,120,120)
$g.DrawString('2',$big,$white,73,26)
$g.DrawString('4',$big,$white,213,26)
$g.DrawString('사 당',$big,$white,390,20)
$g.DrawString('Sadang',$mid,$white,760,29)
$g.DrawString('지하철  Subway',$small,$white,761,89)
$g.DrawString('1',$big,$yellow,1500,14)
$g.DrawString('출구 EXIT',$small,$yellow,1572,67)
$bmp.Save((Join-Path $outDir 'T_SE_StationSign.png'),[Drawing.Imaging.ImageFormat]::Png)
$g.Dispose();$bmp.Dispose()
foreach($o in @($white,$yellow,$green,$blue,$big,$small,$mid)){$o.Dispose()}
