FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema necessárias para build123d/OCP
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglu1-mesa \
    libx11-6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro para aproveitar cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto da aplicação
COPY . .

# Expõe porta do Streamlit
EXPOSE 8501

# Comando de execução
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
