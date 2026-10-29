FROM python:3.12-slim
WORKDIR /app
COPY public_server.py catalog.json datasets.json ./
ENV PORT=8000 HOST=0.0.0.0
EXPOSE 8000
CMD ["python3", "public_server.py"]
