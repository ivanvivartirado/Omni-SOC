Pasos para hacer un Bind9 DNS funcional:

1- Editar named.conf.options

2- Generar clave keygen...
tsig-keygen -a hmac-sha256 kea-bind-key

3- Definir las Zonas locales en Bind9
sudo nano /etc/bind/named.conf.local

4- Crear los archivos base de las Zonas
sudo nano /var/lib/bind/db.laboratorio.local

5- Crear archivo zona inversa:

6- Añadir permisos al usuario 'Bind9' para poder modificarlos:
sudo chown -R bind:bind /var/lib/bind/

7- Verificar y reiniciar:
sudo named-checkconf
// En caso que no devuelva ningun texto, siguiente comando para finalizar la configuración:
sudo systemctl restart bind9
sudo systemctl enable bind9
