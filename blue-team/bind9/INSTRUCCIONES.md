Pasos para hacer un Bind9 DNS funcional:

1- Editar named.conf.options

2- Generar la clave TSIG en un fichero aparte (NO se versiona, *.key está en .gitignore):
sudo tsig-keygen -a hmac-sha256 kea-bind-key | sudo tee /etc/bind/kea-bind-key.key >/dev/null
sudo chown root:bind /etc/bind/kea-bind-key.key && sudo chmod 640 /etc/bind/kea-bind-key.key
En named.conf.local: include "/etc/bind/kea-bind-key.key";

3- Definir las Zonas locales en Bind9
sudo nano /etc/bind/named.conf.local

4- Crear los archivos base de las Zonas
sudo nano /var/lib/bind/db.laboratorio.local

5- Crear archivo zona inversa:

6- Añadir permisos al usuario 'Bind9' para poder modificarlos:
sudo chown -R bind:bind /var/lib/bind/

7- Verificar y reiniciar:
sudo named-checkconf

8- Editar una zona con DDNS activo: sudo rndc freeze <zona> → editar y subir serial → sudo rndc thaw <zona>

// En caso que no devuelva ningun texto, siguiente comando para finalizar la configuración:
sudo systemctl restart bind9
sudo systemctl enable bind9
