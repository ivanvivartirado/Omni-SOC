#!/bin/bash
# ============================================================
# backup.sh — Copia de seguridad semanal
# Ubicación: /home/Omni-SOC/scripts/backup.sh
# Programado: viernes a las 18:00 (cron: 0 18 * * 5)
# ============================================================

# --- CONFIGURACIÓN ---

# Directorio donde se guardan las copias (disco externo, NAS, etc.)
# Cada backup va en una subcarpeta con fecha para no pisar anteriores.
BACKUP_DIR="/mnt/backup"

# Sello de fecha: formato AAAA-MM-DD_HHMM (ej: 2026-10-16_1800)
DATE=$(date +%Y-%m-%d_%H%M)

# Archivo de log para verificar que todo va bien
LOG="/var/log/backup.log"

# Cuántos días conservar los backups (los más antiguos se borran)
RETENTION_DAYS=14

# --- EJECUCIÓN ---

# Crear la carpeta de este backup (con -p no falla si ya existe)
mkdir -p "$BACKUP_DIR/$DATE"

# Copia /etc (configuración del sistema)
# -a  = modo archivo (preserva permisos, enlaces, timestamps)
# --delete = elimina en destino lo que ya no existe en origen (copia espejo)
rsync -a --delete /etc/ "$BACKUP_DIR/$DATE/etc/"

# Copia /home/Omni-SOC (datos del usuario)
rsync -a --delete /home/Omni-SOC/ "$BACKUP_DIR/$DATE/home_Omni-SOC/"

# --- ROTACIÓN ---
# Borra carpetas de backup más antiguas que RETENTION_DAYS
# -maxdepth 1  = solo mira la primera capa (no entra en subcarpetas)
# -type d      = solo directorios
# -mtime +14   = modificados hace más de 14 días
find "$BACKUP_DIR" -maxdepth 1 -type d -mtime +$RETENTION_DAYS -exec rm -rf {} +

# --- LOG ---
# Escribe una línea con fecha y resultado (útil para revisar con tail)
echo "[$(date)] Backup completado en $BACKUP_DIR/$DATE" >> "$LOG"   
