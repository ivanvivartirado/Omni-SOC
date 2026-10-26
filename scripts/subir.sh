#!/usr/bin/env bash
# Omni SOC - Copia las configuraciones del servidor al repo (ordenadas),
# revisa que no se cuele ningun secreto y sube todo a GitHub.
#
# Uso:
#   ./scripts/subir.sh                      -> sube con mensaje automatico
#   ./scripts/subir.sh "kea: añadido pool"  -> sube con tu mensaje
#   ./scripts/subir.sh --ver                -> solo copia y muestra cambios (no sube)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

# ---- Que se copia: ORIGEN en el sistema | DESTINO en el repo ----------------
MAPA=(
  "/etc/kea/kea-dhcp4.conf|blue-team/kea/kea-dhcp4.conf"
  "/etc/bind/named.conf.options|blue-team/bind9/named.conf.options"
  "/etc/bind/named.conf.local|blue-team/bind9/named.conf.local"
  "/var/lib/bind/db.laboratorio.local|blue-team/bind9/db.laboratorio.local"
  "/var/lib/bind/db.1.168.192|blue-team/bind9/db.1.168.192"
  "/etc/ufw/before.rules|blue-team/ufw/before.rules"
  "/etc/ufw/before6.rules|blue-team/ufw/before6.rules"
  "/etc/ufw/user.rules|blue-team/ufw/user.rules"
  "/etc/ufw/user6.rules|blue-team/ufw/user6.rules"
)

SOLO_VER=0
MSG=""
if [[ "${1:-}" == "--ver" ]]; then SOLO_VER=1; else MSG="${1:-}"; fi

echo "==> Copiando configuraciones del sistema al repo"
for par in "${MAPA[@]}"; do
  src="${par%%|*}"; dst="${par##*|}"
  if ! sudo test -e "$src"; then
    echo "   - salto  $src (no existe en esta maquina)"
    continue
  fi
  mkdir -p "$(dirname "$dst")"
  sudo cat "$src" > "$dst"
  echo "   + copiado $src -> $dst"
done

# ---- Quitar secretos conocidos antes de subir -------------------------------
f="blue-team/bind9/named.conf.local"
if [[ -f "$f" ]]; then
  sed -i -E 's/(secret ")[^"]+(")/\1n7lV700K4BJ3YgAcmBvRHTy9AD8sb9IDYivRoRFTNSA=\2/' "$f"
fi
# ---- Comprobacion de seguridad: si hay algo sospechoso, NO se sube ----------
echo "==> Revisando secretos"
if git ls-files -co --exclude-standard -z \
   | grep -zvE '^scripts/(subir\.sh|auditar\.sh)' \
   | xargs -0 -r grep -nIE \
       -e 'secret "[^"]*"' -e 'BEGIN [A-Z ]*PRIVATE KEY' \
       -e '(password|passwd|token)[[:space:]]*[=:][[:space:]]*[^[:space:]]+' \
   | grep -v 'n7lV700K4BJ3YgAcmBvRHTy9AD8sb9IDYivRoRFTNSA='; then
  echo "!! Posible secreto en los ficheros de arriba. No se sube nada."
  exit 1
fi
echo "   OK, sin secretos"
# ---- Git --------------------------------------------------------------------
if [[ -z "$(git status --porcelain)" ]]; then
  echo "==> Nada que subir: el repo ya esta al dia."
  exit 0
fi

echo "==> Cambios:"
git status --short

if [[ $SOLO_VER -eq 1 ]]; then
  echo "==> Modo --ver: no se ha hecho commit ni push."
  exit 0
fi

# ---- Quien eres: el commit saldra a nombre de esa persona -------------------
# Rellena nombre y email de cada uno (el email noreply sale de GitHub > Settings > Emails)
declare -A NOMBRE=( [ivan]="Ivan Vivar"  [iker]="Iker Sanchez" )
declare -A EMAIL=(  [ivan]="183842281+ivaanv23@users.noreply.github.com"
                    [iker]="195279356+ikersafu@users.noreply.github.com" )

QUIEN="${OMNISOC_USER:-}"
if [[ -z "$QUIEN" ]]; then
  echo "==> ¿Quién sube los cambios?"
  select QUIEN in "${!NOMBRE[@]}"; do [[ -n "$QUIEN" ]] && break; done
fi
if [[ -z "${NOMBRE[$QUIEN]:-}" ]]; then
  echo "!! Usuario desconocido: $QUIEN" >&2; exit 1
fi
export GIT_AUTHOR_NAME="${NOMBRE[$QUIEN]}"  GIT_AUTHOR_EMAIL="${EMAIL[$QUIEN]}"
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME" GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
echo "==> Subiendo como: $GIT_AUTHOR_NAME <$GIT_AUTHOR_EMAIL>"

git add -A
git commit -m "${MSG:-sync: configs $(date '+%F %H:%M') desde $(hostname)}"
git pull --rebase --autostash
git push origin HEAD
echo "==> Subido a GitHub."

