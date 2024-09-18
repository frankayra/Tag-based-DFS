# Usa la imagen base de Python
FROM python:3.12.5-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar los archivos del proyecto al contenedor
COPY . /app
COPY requirements.txt /app

# Instalar dependencias listadas en requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# EXPOSE 3000
EXPOSE 50051


# Levantar el server
CMD ["python", "server.py"]
