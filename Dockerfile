FROM python:3.8.10

# Etiqueta del creador
LABEL maintainer="Gaston Ciancio"

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos locales al contenedor
COPY . .

# Instala las dependencias de Python
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Descarga los modelos de spaCy
RUN python3 -m spacy download en

# Comando por defecto para ejecutar la aplicación cuando el contenedor se inicia
CMD ["python3", "main.py"]
