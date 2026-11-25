param([string]$Destination = "$env:LOCALAPPDATA\InclusieveCoach\modellen")
$ErrorActionPreference = "Stop"
$models = @{
    "vosk-model-small-nl-0.22" = "039811c3b829de64e4f123a9f684a53784005b212a346ac0b899dc7efce2ed0a"
    "vosk-model-spk-0.4" = "a74d8f51144484813e16af689bb0f916b7a111e2347f467c4933c1166097b5a7"
}
foreach ($name in $models.Keys) {
    $archive = Join-Path $env:TEMP "$name.zip"
    Invoke-WebRequest "https://alphacephei.com/vosk/models/$name.zip" -OutFile $archive
    if ((Get-FileHash $archive).Hash -ne $models[$name]) { throw "Onjuiste modelchecksum" }
    Expand-Archive $archive $Destination -Force
    Remove-Item $archive
}
