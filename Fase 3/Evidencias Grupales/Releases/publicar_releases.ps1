# Publica en GitHub un release por cada sprint de SITRAFO.
# Requisitos (una sola vez):  winget install --id GitHub.cli   y luego   gh auth login
# Uso, desde PowerShell:
#   powershell -ExecutionPolicy Bypass -File "C:\Users\Benja\Documents\CAPSTONE\SITRAFO\Fase 3\Evidencias Grupales\Releases\publicar_releases.ps1"

$ErrorActionPreference = "Stop"
Set-Location "C:\Users\Benja\Documents\CAPSTONE\SITRAFO"
git pull

$notas = "Fase 3\Evidencias Grupales\Releases"
$releases = @(
    @{ tag = "v0.0-sprint0"; sha = "714b4029b8e15d7039a11682e531d5bc6692c111"; titulo = "Sprint 0: Arquitectura y preparación técnica" },
    @{ tag = "v0.1-sprint1"; sha = "96cd127782d8f4909497a8bfa8c78ed104a3a695"; titulo = "Sprint 1: Desarrollo de las 14 historias" },
    @{ tag = "v0.2-sprint2"; sha = "21b2ec254a14d915118e46f29df47323f64543dc"; titulo = "Sprint 2: Despliegue, documentación y calidad en producción" },
    @{ tag = "v0.3-sprint3"; sha = "3805bfea2f220df0a9dea783a2844720899ea017"; titulo = "Sprint 3: Tres APIs públicas propias" },
    @{ tag = "v1.0-fase2";   sha = "7525fc50a5b0f5551273cc3ac1532475979ef599"; titulo = "Entrega de la Fase 2" }
)

foreach ($r in $releases) {
    if (-not (git tag -l $r.tag)) { git tag -a $r.tag $r.sha -m $r.titulo }
    git push origin $r.tag
    gh release create $r.tag --verify-tag --title $r.titulo --notes-file "$notas\$($r.tag).md"
}

Write-Host ""
Write-Host "Listo: releases publicados en https://github.com/benjamindelgado-dev/SITRAFO/releases"

# ---------------------------------------------------------------------------
# Release final de la Fase 3: ejecutar SOLO el dia de la entrega final, despues
# de subir el ultimo cambio (queda en el commit mas reciente de main):
#
#   git pull
#   git tag -a v2.0-fase3 -m "Sprint 4: Cierre del proyecto (Fase 3)"
#   git push origin v2.0-fase3
#   gh release create v2.0-fase3 --verify-tag --latest --title "Sprint 4: Cierre del proyecto (Fase 3)" --notes-file "Fase 3\Evidencias Grupales\Releases\v2.0-fase3.md"
# ---------------------------------------------------------------------------
