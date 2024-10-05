# Usa la imagen base de Python
FROM python:3.12.5-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /usr/src/app

# Copiar el archivo de dependencias
COPY Server/requirements.txt ./

# Instalar las dependencias
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY Server/ ./

# Instalar watchdog para reinicio automático
RUN pip install watchdog

# Exponer el puerto que tu aplicación usará (ajusta según tu servidor)
EXPOSE 50051

# Comando para ejecutar la aplicación con watchdog
CMD ["watchmedo", "auto-restart", "--directory=.", "--pattern=*.py", "--recursive", "--", "python", "server.py", "docker-server"]