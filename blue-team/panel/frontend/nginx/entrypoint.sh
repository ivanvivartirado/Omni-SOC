#!/bin/sh
# Genera un certificado autofirmado si no se ha montado uno propio en /etc/nginx/certs.
set -eu
CERT_DIR=/etc/nginx/certs
if [ ! -s "$CERT_DIR/panel.crt" ] || [ ! -s "$CERT_DIR/panel.key" ]; then
  mkdir -p "$CERT_DIR"
  CN="${PANEL_HOSTNAME:-omni-server.omnisoc.local}"
  echo "omni-soc: generando certificado autofirmado para $CN"
  openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
    -subj "/CN=$CN/O=Omni SOC" \
    -addext "subjectAltName=DNS:$CN,DNS:localhost,IP:127.0.0.1${PANEL_IP:+,IP:$PANEL_IP}" \
    -keyout "$CERT_DIR/panel.key" -out "$CERT_DIR/panel.crt" 2>/dev/null
  chmod 600 "$CERT_DIR/panel.key"
fi
