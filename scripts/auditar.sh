#!/usr/bin/env bash
set -uo pipefail
umask 077

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

FECHA="$(date +%Y%m%d-%H%M%S)"
LOG="$REPO/auditoria-$FECHA.log"

# El log puede contener información de red. Permisos solo para el propietario.
exec 3>&1
exec > >(tee "$LOG") 2>&1

seccion() {
    printf '\n\n========== %s ==========\n' "$1"
}

comando() {
    local descripcion="$1"
    shift
    printf '\n--- %s ---\n' "$descripcion"
    "$@" 2>&1 || echo "[AVISO] Comando con error: $descripcion"
}

archivo() {
    local f="$1"
    printf '\n--- Archivo: %s ---\n' "$f"
    if [[ -f "$f" ]]; then
        # No imprimir claves ni posibles credenciales.
        sed -E           -e '/^[[:space:]]*(secret|password|passwd|token|api[_-]?key)[[:space:]]/Id'           -e 's#(secret[[:space:]]+")([^"]*)(")#\1[REDACTADO]\3#Ig'           "$f"
    else
        echo "[NO EXISTE]"
    fi
}

seccion "INFORMACION GENERAL"
date -Is
hostname
id
printf 'Repositorio: %s\n' "$REPO"
printf 'Log: %s\n' "$LOG"
uname -a
if command -v lsb_release >/dev/null 2>&1; then
    lsb_release -ds
fi

seccion "GIT: RAMA, ESTADO Y RESUMEN"
git branch --show-current
git status --short
git --no-pager diff --stat
git --no-pager diff --check
git log -5 --oneline --decorate
git remote -v | sed -E 's#(https?://)[^/@]+:[^/@]+@#\1[REDACTADO]@#g'

seccion "ESTRUCTURA DEL REPOSITORIO"
find . -maxdepth 4 -type f   -not -path './.git/*'   -not -name 'auditoria-*.log'   -not -name '*.bak.*'   -printf '%p (%s bytes)\n' | sort

seccion "GITIGNORE Y ATRIBUTOS"
archivo .gitignore
archivo .gitattributes

seccion "README Y DOCUMENTACION"
sed -n '1,180p' README.md 2>/dev/null || true
sed -n '1,180p' docs/propuesta.md 2>/dev/null || true

seccion "CONFIGURACIONES VERSIONADAS: BIND9 Y KEA"
for f in   blue-team/bind9/named.conf.local   blue-team/bind9/named.conf.options   blue-team/bind9/INSTRUCCIONES.md   blue-team/bind9/db.laboratorio.local   blue-team/bind9/db.1.168.192   blue-team/kea/kea-dhcp4.conf; do
    archivo "$f"
done

seccion "CONFIGURACIONES VERSIONADAS: UFW"
for f in   blue-team/ufw/before.rules   blue-team/ufw/before6.rules   blue-team/ufw/user.rules   blue-team/ufw/user6.rules; do
    if [[ -f "$f" ]]; then
      printf '\n--- %s: resumen de reglas ---\n' "$f"
      grep -E '^\*|^:|^-A |^-I ' "$f" |
        sed -E           -e 's/(--dport[[:space:]]+[0-9]+).*/\1 [resto omitido]/'           -e 's/(--dports[[:space:]]+)[0-9,]+/\1[PUERTOS]/'           -e 's/(--log-prefix[[:space:]]+)"[^"]*"/\1"[PREFIJO]"/'
    else
      echo "$f: [NO EXISTE]"
    fi
done

seccion "ESTADO DEL SISTEMA Y RED"
comando "Sistema operativo" cat /etc/os-release
comando "Interfaces e IP" ip -brief address
comando "Rutas" ip route
comando "Puertos escuchando" ss -lntup
comando "Resolucion DNS local" resolvectl status
comando "Uso de disco" df -h /

seccion "SERVICIOS INSTALADOS Y ACTIVOS"
for servicio in bind9 named kea-dhcp4-server ufw; do
    if systemctl list-unit-files "${servicio}.service" --no-legend 2>/dev/null |
        grep -q "${servicio}.service"; then
        systemctl is-enabled "$servicio" 2>&1 || true
        systemctl is-active "$servicio" 2>&1 || true
    else
        echo "$servicio: unidad no encontrada con ese nombre"
    fi
done

seccion "BIND9: VALIDACION Y CONFIGURACION ACTIVA"
if command -v named-checkconf >/dev/null 2>&1; then
    comando "named-checkconf" sudo -n named-checkconf
    comando "named-checkconf -z" sudo -n named-checkconf -z
else
    echo "named-checkconf no instalado"
fi

for f in   /etc/bind/named.conf   /etc/bind/named.conf.local   /etc/bind/named.conf.options; do
    if [[ -r "$f" ]]; then
        archivo "$f"
    else
        echo "$f: no legible sin privilegios"
    fi
done

for f in   /var/lib/bind/db.laboratorio.local   /var/lib/bind/db.1.168.192; do
    if [[ -r "$f" ]]; then
        archivo "$f"
    else
        echo "$f: no legible sin privilegios"
    fi
done

if command -v named-checkzone >/dev/null 2>&1; then
    comando "Zona directa activa"       sudo -n named-checkzone laboratorio.local       /var/lib/bind/db.laboratorio.local
    comando "Zona inversa activa"       sudo -n named-checkzone 1.168.192.in-addr.arpa       /var/lib/bind/db.1.168.192
fi

seccion "KEA DHCP: VALIDACION Y CONFIGURACION ACTIVA"
if command -v kea-dhcp4 >/dev/null 2>&1; then
    comando "Validacion Kea activa"       sudo -n kea-dhcp4 -t -c /etc/kea/kea-dhcp4.conf
else
    echo "kea-dhcp4 no instalado"
fi

if [[ -r /etc/kea/kea-dhcp4.conf ]]; then
    archivo /etc/kea/kea-dhcp4.conf
else
    echo "/etc/kea/kea-dhcp4.conf no legible sin privilegios"
fi

seccion "COMPARACION CONFIGURACIONES VERSIONADAS Y ACTIVAS"
for par in   "blue-team/bind9/named.conf.local|/etc/bind/named.conf.local"   "blue-team/bind9/named.conf.options|/etc/bind/named.conf.options"   "blue-team/bind9/db.laboratorio.local|/var/lib/bind/db.laboratorio.local"   "blue-team/bind9/db.1.168.192|/var/lib/bind/db.1.168.192"   "blue-team/kea/kea-dhcp4.conf|/etc/kea/kea-dhcp4.conf"   "blue-team/ufw/before.rules|/etc/ufw/before.rules"   "blue-team/ufw/before6.rules|/etc/ufw/before6.rules"   "blue-team/ufw/user.rules|/etc/ufw/user.rules"   "blue-team/ufw/user6.rules|/etc/ufw/user6.rules"; do
    repo_file="${par%%|*}"
    active_file="${par#*|}"
    printf '\n--- %s <-> %s ---\n' "$repo_file" "$active_file"
    if [[ ! -f "$repo_file" ]]; then
        echo "Falta archivo versionado"
    elif [[ ! -r "$active_file" ]]; then
        echo "Configuracion activa ausente o no legible"
    elif sudo -n test -r "$active_file" 2>/dev/null; then
        if sudo -n cmp -s "$repo_file" "$active_file"; then
            echo "COINCIDEN"
        else
            echo "DIFERENCIAS (se muestra solo el resumen)"
            sudo -n diff -u "$repo_file" "$active_file" |
              sed -E                 -e '/^[+-].*(secret|password|passwd|token|key)[[:space:]]/Id'                 -e 's/(secret[[:space:]]+")([^"]*)(")/\1[REDACTADO]\3/Ig' |
              head -80 || true
        fi
    else
        echo "No se pudo leer la configuracion activa con sudo sin contraseña"
    fi
done

seccion "UFW: ESTADO ACTIVO"
if command -v ufw >/dev/null 2>&1; then
    comando "Estado UFW" sudo -n ufw status verbose
    comando "Estado UFW numerado" sudo -n ufw status numbered
else
    echo "ufw no instalado"
fi

seccion "PAQUETES RELACIONADOS"
if command -v dpkg-query >/dev/null 2>&1; then
    dpkg-query -W -f='${binary:Package} ${Version} ${db:Status-Status}\n'       'bind9*' 'kea-dhcp4*' 'ufw' 'ansible*' 2>/dev/null || true
fi

seccion "ANSIBLE Y SCRIPTS"
if command -v ansible-playbook >/dev/null 2>&1; then
    ansible-playbook --version | head -5
else
    echo "Ansible no está instalado o no está en PATH"
fi

find infra scripts -maxdepth 4 -type f   -not -name 'auditoria-*.log' -print 2>/dev/null | sort || true

if [[ -f scripts/subir.sh ]]; then
    bash -n scripts/subir.sh && echo "subir.sh: sintaxis OK" ||
      echo "subir.sh: ERROR de sintaxis"
fi

if [[ -f scripts/subir.sh ]]; then
    echo "--- scripts/subir.sh (contenido) ---"
    sed -n '1,160p' scripts/subir.sh
fi

seccion "POSIBLES SECRETOS: SOLO NOMBRES DE ARCHIVO Y LINEAS, SIN VALORES"
# No muestra el contenido de las líneas detectadas.
grep -RInE   --exclude-dir=.git   --exclude='auditoria-*.log'   --exclude='*.bak.*'   --exclude='*.png'   --exclude='*.jpg'   --exclude='*.jpeg'   '(secret[[:space:]]+"|password[[:space:]]*[:=]|passwd[[:space:]]*[:=]|token[[:space:]]*[:=]|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|CAMBIAR_POR_TU_CLAVE)'   . 2>/dev/null |
  sed -E 's/^([^:]+:[0-9]+):.*/\1: [LINEA CON PATRON SENSIBLE; VALOR OMITIDO]/' |
  head -100 || true

seccion "FIN"
echo "Auditoria finalizada: $LOG"
echo "El log se ha creado con permisos privados."
echo "No se han aplicado configuraciones ni publicado cambios."

exec 1>&3 3>&-
printf '\nLog generado: %s\n' "$LOG"
