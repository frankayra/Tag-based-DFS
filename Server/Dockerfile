# Usar una imagen base de Python
FROM python:3.11-slim
# Establecer un directorio de trabajo
WORKDIR /app
# Copiar el archivo los archivos en la imagen
COPY . ./server.py
# Ejecutar el script server.py cuando se inicie el contenedor
ENTRYPOINT ["python", "./server.py"]
