#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

SOLO_VER=0
MSG=""

if [[ "${1:-}" == "--ver" ]]; then
  SOLO_VER=1
else
  MSG="${1:-}"
fi

# --ver es de solo lectura: no copia archivos ni modifica Git.
if [[ "$SOLO_VER" -eq 1 ]]; then
  echo "==> Vista previa: no se modifica ningún archivo"
  git status --short
  git diff --check
  echo "==> Fin de la vista previa"
  exit 0
fi

echo "Este script no publica automáticamente cambios."
echo "Revisa y prepara los archivos manualmente con Git."
echo "Usa ./scripts/subir.sh --ver para consultar el estado."
echo "No se han copiado archivos ni realizado commits."
exit 0
