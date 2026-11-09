# Contexto de build = raiz do repositório (precisa enxergar db/ além de app_principal/)
FROM python:3.10-slim
WORKDIR /app
COPY app_principal/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app_principal/ .
COPY db/ /app/db/
EXPOSE 80
CMD ["python", "app.py"]
