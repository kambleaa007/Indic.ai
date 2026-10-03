$ErrorActionPreference = "Stop"
$base = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
$voices = @(
    @{ lang = "mr"; locale = "mr_IN"; name = "google" },
    @{ lang = "te"; locale = "te_IN"; name = "maya" },
    @{ lang = "te"; locale = "te_IN"; name = "venkatesh" },
    @{ lang = "bn"; locale = "bn_BD"; name = "google" },
    @{ lang = "ml"; locale = "ml_IN"; name = "arjun" },
    @{ lang = "ur"; locale = "ur_PK"; name = "fasih" },
    @{ lang = "hi"; locale = "hi_IN"; name = "priyamvada" }
)

New-Item -ItemType Directory -Force -Path ".\voices" | Out-Null

foreach ($v in $voices) {
    $stem = "$($v.locale)-$($v.name)-medium"
    $dir = "$($v.lang)/$($v.locale)/$($v.name)/medium"
    foreach ($ext in @("onnx.json", "onnx")) {
        $out = ".\voices\$stem.$ext"
        if (Test-Path $out) { Write-Output "skip  $stem.$ext"; continue }
        Write-Output "get   $stem.$ext"
        Invoke-WebRequest -Uri "$base/$dir/$stem.$ext" -OutFile $out
    }
}
Write-Output "--- done ---"
Get-ChildItem ".\voices\*.onnx" | Select-Object Name, @{ n = "MB"; e = { [math]::Round($_.Length / 1MB, 1) } } | Format-Table -AutoSize
