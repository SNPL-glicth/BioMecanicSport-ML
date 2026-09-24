# BioMecanicSport - Microservicio de Machine Learning & Visión Artificial

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-snplglicth%2Fbiomecanicsport--ml-blue?style=flat&logo=docker&logoColor=white)](https://hub.docker.com/r/snplglicth/biomecanicsport-ml)
[![Architecture](https://img.shields.io/badge/Architecture-Hexagonal-orange?style=flat)](#arquitectura)

Microservicio desacoplado y especializado en el procesamiento cinemático, cálculo biomecánico y análisis de movimiento en tiempo real para la plataforma **BioMecanicSport**.

---

## 📐 Arquitectura

El microservicio está implementado siguiendo los principios de la **Arquitectura Hexagonal (Puertos y Adaptadores)** para garantizar alta cohesión, bajo acoplamiento e independencia del framework web:

```
BioMecanicSport-ML/
├── application/             # Capa de Aplicación: Casos de uso
│   ├── __init__.py
│   └── video_use_case.py    # Orquestación de análisis cinemático
├── domain/                  # Capa de Dominio: Lógica pura matemática / física
│   ├── __init__.py
│   └── biomechanics.py      # Entidades y cálculo cinemático de ángulos
├── infrastructure/          # Capa de Infraestructura: Adaptadores y Frameworks
│   ├── api/                 # Adaptador HTTP (FastAPI Routers y DTOs)
│   │   ├── __init__.py
│   │   └── routers.py
│   └── main.py              # Configuración FastAPI, CORS y Middlewares
├── Dockerfile               # Contenedorización optimizada en Python 3.12-slim
├── requirements.txt         # Dependencias principales del microservicio
└── main.py                  # Punto de entrada ASGI (Uvicorn)
```

- **Domain (`domain/`)**: Reglas de negocio puras, cálculo de ángulos articulares 2D con `atan2` y validación de rangos de seguridad anatómica. Sin dependencias externas.
- **Application (`application/`)**: Orquesta la conversión de DTOs a entidades de dominio y coordina el flujo de análisis deportivo.
- **Infrastructure (`infrastructure/`)**: Adaptadores REST con FastAPI, validación de esquemas con Pydantic, serialización y middlewares.

---

## 🚀 Tecnologías

- **Python 3.12**
- **FastAPI**: Framework web asíncrono de alto rendimiento.
- **OpenCV (headless)** & **NumPy**: Procesamiento numérico y matricial de coordenadas y video.
- **Pydantic v2**: Validación estricta y esquemas DTO.
- **Uvicorn**: Servidor ASGI con soporte HTTP y WebSockets.
- **Docker**: Empaquetado ligero y reproducible.

---

## 📡 Endpoints de la API

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET` | `/` | Información general, estado del microservicio y arquitectura |
| `GET` | `/health` | Healthcheck para monitoreo y orquestadores (Docker / K8s) |
| `GET` | `/docs` | Documentación interactiva interactiva OpenAPI / Swagger UI |
| `GET` | `/redoc` | Documentación técnica alternativa ReDoc |
| `POST` | `/analisis/angulo` | Cálculo cinemático de ángulo articular y evaluación de alerta lesiva |
| `GET` | `/analisis/simulacion` | Simulación rápida de flexión articular preconfigurada |

### Ejemplo: Cálculo de Ángulo Articular

**POST** `/analisis/angulo`

```json
{
  "nombre_articulacion": "Rodilla Derecha",
  "punto_origen": {"x": 120.5, "y": 210.0, "z": 0.0},
  "vertice": {"x": 122.0, "y": 320.0, "z": 0.0},
  "punto_destino": {"x": 195.0, "y": 320.0, "z": 0.0}
}
```

**Respuesta (200 OK):**

```json
{
  "articulacion": "Rodilla Derecha",
  "angulo_grados": 90.81,
  "alerta_riesgo_lesion": false,
  "diagnostico_tecnico": "Óptimo: Rango cinemático dentro de los estándares biomecánicos.",
  "timestamp": "2026-09-24T19:50:00.000000"
}
```

---

## 🛠️ Ejecución Local

### Opción 1: Entorno Virtual Python

```bash
# 1. Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Linux/macOS
# .\venv\Scripts\activate   # En Windows

# 2. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 3. Iniciar el servidor de desarrollo
uvicorn infrastructure.main:app --host 0.0.0.0 --port 8001 --reload
```

Accede a la API en: [http://localhost:8001/docs](http://localhost:8001/docs)

---

## 🐳 Docker & Despliegue

### Construcción Local de la Imagen

```bash
docker build -t snplglicth/biomecanicsport-ml:latest .
```

### Ejecución del Contenedor en Solitario

```bash
docker run -d \
  --name biomecanic_ml \
  -p 8001:8001 \
  snplglicth/biomecanicsport-ml:latest
```

### Publicación en Docker Hub

```bash
# 1. Autenticarse en Docker Hub
docker login

# 2. Subir la imagen
docker push snplglicth/biomecanicsport-ml:latest
```

---

## 🔗 Integración con el Ecosistema BioMecanicSport

Este microservicio es consumido directamente por el backend principal a través del `docker-compose.yml` del repositorio central:

```yaml
  ml_service:
    image: snplglicth/biomecanicsport-ml:latest
    container_name: biomecanic_ml_service
    restart: unless-stopped
    ports:
      - "${ML_SERVICE_PORT:-4001}:8001"
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - biomecanic_network
```