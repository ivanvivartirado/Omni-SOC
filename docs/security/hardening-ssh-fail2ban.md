# Hardening SSH y Fail2ban – Omni-SOC

## 1. Servidor

- Hostname: omnisoc-server
- Sistema: Ubuntu 26.04.1 LTS
- Red administrativa: 192.168.15.0/24

## 2. Configuración SSH

Archivo: `/etc/ssh/sshd_config.d/00-omnisoc-hardening.conf`

```text
MaxAuthTries 3
PubkeyAuthentication yes
PermitRootLogin prohibit-password
```

Configuración efectiva verificada:

- MaxAuthTries: 3
- PubkeyAuthentication: yes
- PermitRootLogin: prohibit-password
- PasswordAuthentication: yes

La autenticación por contraseña permanece habilitada deliberadamente.

## 3. Acceso mediante clave pública

Equipo administrativo: snowden-105

Usuario remoto: ivan

Método: Ed25519

Autenticación mediante clave comprobada satisfactoriamente desde el equipo cliente.

## 4. Fail2ban

Archivo: `/etc/fail2ban/jail.d/omnisoc-sshd.local`

Jail: sshd

- enabled: true
- port: 22
- backend: systemd
- maxretry: 5
- findtime: 600 segundos
- bantime: 3600 segundos

IP administrativa excluida:

- 192.168.15.105

## 5. Verificaciones

- `sshd -t`: configuración válida.
- `fail2ban-client -t`: configuración válida.
- Fail2ban: enabled y active.
- Jail sshd: activo.
- Autenticación SSH por clave: verificada.
- Repositorio Omni-SOC: sin cambios pendientes antes de documentar.

## 6. Consideraciones

La autenticación por contraseña sigue habilitada. No se considera completada su desactivación.

No se ha realizado una prueba de bloqueo real de Fail2ban.

Las configuraciones operativas permanecen en `/etc` y no se incluyen sus archivos directamente en el repositorio.
