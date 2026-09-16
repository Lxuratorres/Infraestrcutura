# Ejercicio 1: Mi Primera Imagen Docker

Aplicación web mínima en Python con Flask, empaquetada en una imagen Docker construida desde cero, aplicando optimización de caché y ejecución con usuario no-root.

**Imagen:** `lxuratorres/flask-app-ejercicio1:1.0`

## Estructura

```
ejercicio1/
├── app.py              # Aplicación Flask con las rutas / y /health
├── Dockerfile          # Instrucciones para construir la imagen
├── docker-compose.yml  # Construye y levanta el contenedor
├── requirements.txt    # Dependencias de Python
└── README.md
```

## Requisitos

- Docker y Docker Compose instalados.

## Ejecución

Desde esta carpeta:

```bash
docker compose up -d
```

Este comando construye la imagen a partir del Dockerfile y levanta el contenedor en segundo plano. Espera unos segundos a que Flask arranque antes de probar.

### Alternativa con docker build / docker run

```bash
docker build -t lxuratorres/flask-app-ejercicio1:1.0 .
docker run -d --name flask_ejercicio1 -p 5000:5000 lxuratorres/flask-app-ejercicio1:1.0
```

## Verificación

```bash
curl http://localhost:5000/
# {"hostname":"<id-contenedor>","ip_address":"<ip>","message":"Hola desde Flask!","status":"success"}

curl http://localhost:5000/health
# {"app":"up and running","status":"healthy"}
```

Ver estado, logs y usuario del proceso:

```bash
docker compose ps
docker compose logs
docker compose exec ejercicio1-app whoami   # debe mostrar: appuser
```

Detener y eliminar el contenedor:

```bash
docker compose down
```

## Análisis de la imagen

```bash
docker history lxuratorres/flask-app-ejercicio1:1.0
docker inspect lxuratorres/flask-app-ejercicio1:1.0
```

### 1. ¿Cuántas capas tiene la imagen y a qué instrucción corresponde cada una?

Según `docker history`, la imagen tiene **20 pasos**: 10 provienen de la imagen base `python:3.11-slim` y 10 de nuestro Dockerfile. De ellos, **9 son capas con contenido** en el sistema de archivos (4 de la base y 5 propias); el resto son capas de metadatos de 0 B.

Capas generadas por nuestro Dockerfile:

| Instrucción | Tamaño | Tipo |
|---|---|---|
| LABEL maintainer, description, version | 0 B | Metadatos |
| ENV FLASK_APP, FLASK_RUN_HOST | 0 B | Metadatos |
| WORKDIR /app | 8.19 kB | Archivos (crea el directorio) |
| COPY requirements.txt | 12.3 kB | Archivos |
| RUN pip install --no-cache-dir | 18.3 MB | Archivos (la capa más pesada) |
| COPY app.py | 12.3 kB | Archivos |
| RUN useradd + chown | 81.9 kB | Archivos |
| USER appuser | 0 B | Metadatos |
| EXPOSE 5000 | 0 B | Metadatos |
| CMD flask run | 0 B | Metadatos |

Capas heredadas de la imagen base con contenido: sistema Debian (87.5 MB), paquetes del sistema con apt (13.2 MB), instalación de Python 3.11.16 (48.8 MB) y enlaces simbólicos (16.4 kB).

Las instrucciones que modifican el sistema de archivos (WORKDIR, COPY, RUN) generan capas con contenido; LABEL, ENV, USER, EXPOSE y CMD solo modifican la configuración de la imagen.

**Datos de `docker inspect`:** usuario `appuser`, puerto expuesto `5000/tcp`, tamaño de 54.2 MB comprimida y 222 MB en disco. La aplicación agrega solo 22 MB sobre la imagen base, principalmente por las dependencias de Flask.

### 2. ¿Por qué se copia requirements.txt antes que app.py?

Docker guarda cada capa en caché y la reutiliza si ni la instrucción ni sus archivos cambiaron. Cuando una capa cambia, todas las siguientes se reconstruyen.

Las dependencias cambian muy poco, mientras que `app.py` cambia con frecuencia. Al copiar primero `requirements.txt` e instalar las dependencias, un cambio en el código solo invalida la capa de `COPY app.py` y las posteriores; la capa de `pip install` (18.3 MB) se reutiliza. Esto hace que las reconstrucciones sean mucho más rápidas. Si se copiara todo junto al inicio, cualquier cambio en el código obligaría a reinstalar todas las dependencias.

### 3. Diferencia de tamaño entre python:3.11, python:3.11-slim y python:3.11-alpine

| Imagen | Tamaño en disco | Tamaño de descarga (comprimido) |
|---|---|---|
| python:3.11 | 1.61 GB | 427 MB |
| python:3.11-slim | 200 MB | 50.7 MB |
| python:3.11-alpine | 93.4 MB | 23.7 MB |

La imagen `slim` ocupa aproximadamente 8 veces menos espacio que la imagen completa, mientras que `alpine` es cerca de la mitad de `slim`.

Se eligió **python:3.11-slim**. La imagen completa incluye compiladores y herramientas que no se necesitan para ejecutar la aplicación, lo que aumenta el tiempo de descarga y la superficie de ataque. Alpine es la más pequeña, pero usa `musl` en lugar de `glibc`, por lo que muchos paquetes de Python no tienen binarios precompilados y deben compilarse, lo que puede alargar la construcción y terminar aumentando el tamaño final. Slim ofrece el mejor equilibrio entre tamaño, seguridad y compatibilidad.

### 4. ¿Cuál es el riesgo de ejecutar procesos como root dentro de un contenedor?

Si un atacante explota una vulnerabilidad en la aplicación, obtiene los mismos permisos que el proceso. Como root, podría modificar o borrar cualquier archivo del contenedor, instalar herramientas maliciosas y, si existe una falla en el runtime o una configuración insegura (volúmenes montados, contenedor privilegiado), intentar escapar al host con privilegios elevados, ya que por defecto el root del contenedor corresponde al root del host.

Por eso la imagen crea el usuario `appuser` con `useradd` y cambia a él con `USER`, aplicando el principio de mínimo privilegio. Se comprobó con `docker compose exec ejercicio1-app whoami`, que devuelve `appuser`.