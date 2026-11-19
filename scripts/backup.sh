#!/bin/bash
# ============================================================
# backup.sh — Copia de seguridad semanal
# Ubicación: /home/Omni-SOC/scripts/backup.sh
# Programado: viernes 18:00 en el crontab de ROOT (sudo crontab -e)
#   0 18 * * 5 /home/Omni-SOC/scripts/backup.sh
# ============================================================
set -uo pipefail

# --- CONFIGURACIÓN ---
BACKUP_DIR="/mnt/backup"                 # disco externo / NAS (debe estar montado)
DATE=$(date +%Y-%m-%d_%H%M)
DEST="$BACKUP_DIR/$DATE"
LATEST="$BACKUP_DIR/latest"              # enlace simbólico al último backup
LOG="/var/log/backup.log"
RETENTION_DAYS=14                        # backups locales
SOURCES=(/etc /home/Omni-SOC)

# Copia fuera de la máquina (dejar vacío "" para desactivarla)
RCLONE_REMOTE="gdrive-crypt:"
REMOTE_RETENTION="60d"                   # cuánto se conservan en la nube

# --- FUNCIONES ---
log()  { echo "[$(date '+%F %T')] $*" >> "$LOG"; }
fail() { log "ERROR: $*"; exit 1; }

# --- COMPROBACIONES ---
[ "$(id -u)" -eq 0 ]          || fail "hay que ejecutarlo como root"
mountpoint -q "$BACKUP_DIR"   || fail "$BACKUP_DIR no está montado, abortando"
mkdir -p "$DEST"              || fail "no se pudo crear $DEST"

# --- COPIA LOCAL (incremental con hardlinks) ---
for SRC in "${SOURCES[@]}"; do
    NAME=$(echo "${SRC#/}" | tr '/' '_')      # /home/Omni-SOC -> home_Omni-SOC
    OPTS=(-a)
    # Lo que no ha cambiado se enlaza al backup anterior: casi no ocupa espacio
    [ -d "$LATEST/$NAME" ] && OPTS+=(--link-dest="$LATEST/$NAME")
    rsync "${OPTS[@]}" "$SRC/" "$DEST/$NAME/" || fail "rsync de $SRC falló"
done
ln -sfn "$DEST" "$LATEST"
log "OK local: $DEST ($(du -sh "$DEST" | cut -f1))"

# --- ROTACIÓN LOCAL ---
# -mindepth 1 evita evaluar /mnt/backup; -name solo toca carpetas con formato de fecha
find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d \
     -name '20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]_[0-9][0-9][0-9][0-9]' \
     -mtime +"$RETENTION_DAYS" -exec rm -rf {} +

# --- COPIA FUERA DE LA MÁQUINA ---
if [ -n "$RCLONE_REMOTE" ]; then
    TARBALL="/tmp/omnisoc_$DATE.tar.gz"
    # tar conserva permisos y propietarios (rclone por sí solo no)
    tar -czf "$TARBALL" -C "$DEST" . || fail "no se pudo crear $TARBALL"
    rclone copy "$TARBALL" "$RCLONE_REMOTE/" || { rm -f "$TARBALL"; fail "subida a $RCLONE_REMOTE falló"; }
    rm -f "$TARBALL"
    rclone delete "$RCLONE_REMOTE/" --min-age "$REMOTE_RETENTION" || log "AVISO: rotación remota falló"
    log "OK remoto: omnisoc_$DATE.tar.gz -> $RCLONE_REMOTE"
fi

exit 0
