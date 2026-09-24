"""
Adaptador de Entrada (Driving Adapter): Routers HTTP con FastAPI.
Recibe peticiones web, valida esquemas con Pydantic y delega al Caso de Uso.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from application.video_use_case import ProcesarVideoMovimientoUseCase
from application.telemetry_use_case import ProcesarTelemetriaStreamingUseCase

router = APIRouter(prefix="/analisis", tags=["Análisis Biomecánico"])
telemetria_router = APIRouter(tags=["Telemetría en Streaming"])


# Esquemas DTO (Data Transfer Objects) para la capa de presentación
class CoordenadaDTO(BaseModel):
    """Representación de un punto articular en el plano/espacio."""
    x: float = Field(..., description="Posición en eje X (píxeles o normalizada)")
    y: float = Field(..., description="Posición en eje Y (píxeles o normalizada)")
    z: Optional[float] = Field(default=0.0, description="Profundidad estimada en eje Z")


class SolicitudCalculoAnguloDTO(BaseModel):
    """Datos necesarios para calcular el ángulo articular."""
    nombre_articulacion: str = Field(default="Rodilla Derecha", description="Nombre del complejo articular")
    punto_origen: CoordenadaDTO = Field(..., description="Punto A (ej. Cadera)")
    vertice: CoordenadaDTO = Field(..., description="Punto B Vértice (ej. Rodilla)")
    punto_destino: CoordenadaDTO = Field(..., description="Punto C (ej. Tobillo)")


class RespuestaAnalisisDTO(BaseModel):
    """Respuesta serializada con el diagnóstico cinemático."""
    articulacion: str
    angulo_grados: float
    alerta_riesgo_lesion: bool
    diagnostico_tecnico: str
    timestamp: str


# =========================================================================
# DTOs para Telemetría por Streaming (MediaPipe Landmarks)
# =========================================================================
class LandmarkPuntoDTO(BaseModel):
    """Punto articular extraído por MediaPipe u otro detector de pose."""
    name: Optional[str] = Field(default=None, description="Identificador semántico del punto (ej. knee_right)")
    x: float = Field(..., description="Coordenada X normalizada (0.0 a 1.0) o absoluta")
    y: float = Field(..., description="Coordenada Y normalizada (0.0 a 1.0) o absoluta")
    z: Optional[float] = Field(default=0.0, description="Profundidad o componente Z")
    visibility: Optional[float] = Field(default=1.0, description="Confianza o visibilidad del landmark (0.0 a 1.0)")


class SolicitudTelemetriaDTO(BaseModel):
    """Payload de telemetría emitido por el Telemetry Server (WebSocket -> HTTP)."""
    session_id: Optional[str] = Field(default=None, description="Identificador único de la sesión de captura")
    frame_id: Optional[int] = Field(default=None, description="Número de secuencia del frame")
    timestamp: Optional[float] = Field(default=None, description="Marca de tiempo en segundos de la captura")
    articulacion: Optional[str] = Field(default="Rodilla Derecha", description="Nombre de la articulación analizada")
    landmarks: List[LandmarkPuntoDTO] = Field(..., min_length=3, description="Arreglo de coordenadas articulares")


class RespuestaTelemetriaDTO(BaseModel):
    """Diagnóstico cinemático derivado de la telemetría en streaming."""
    status: str
    session_id: str
    frame_id: Optional[int] = None
    articulacion: str
    angulo_grados: float
    alerta_riesgo_lesion: bool
    diagnostico_tecnico: str
    puntos_procesados: int
    timestamp: str


# =========================================================================
# Endpoints de Análisis Biomecánico Convencional
# =========================================================================
@router.post(
    "/angulo",
    response_model=RespuestaAnalisisDTO,
    status_code=status.HTTP_200_OK,
    summary="Calcular ángulo articular",
    description="Calcula el ángulo biomecánico entre tres coordenadas y evalúa el riesgo lesivo."
)
def calcular_angulo(solicitud: SolicitudCalculoAnguloDTO):
    try:
        caso_de_uso = ProcesarVideoMovimientoUseCase()
        resultado = caso_de_uso.ejecutar(
            punto_origen=solicitud.punto_origen.model_dump(),
            vertice_articular=solicitud.vertice.model_dump(),
            punto_destino=solicitud.punto_destino.model_dump(),
            nombre_articulacion=solicitud.nombre_articulacion
        )
        return resultado
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante el procesamiento cinemático: {str(exc)}"
        )


@router.get(
    "/simulacion",
    response_model=RespuestaAnalisisDTO,
    summary="Ejecutar análisis biomecánico simulado",
    description="Endpoint demostrativo con coordenadas de Cadera, Rodilla y Tobillo preestablecidas."
)
def simulacion_movimiento():
    """Simula una flexión de rodilla típica en sentadilla o salto."""
    caso_de_uso = ProcesarVideoMovimientoUseCase()
    resultado = caso_de_uso.ejecutar(
        punto_origen={"x": 100.0, "y": 200.0, "z": 0.0},
        vertice_articular={"x": 100.0, "y": 300.0, "z": 0.0},
        punto_destino={"x": 180.0, "y": 300.0, "z": 0.0},
        nombre_articulacion="Rodilla en Sentadilla (Prueba)"
    )
    return resultado


# =========================================================================
# Endpoint de Ingesta de Telemetría Streaming (Consumido por Telemetry Server)
# =========================================================================
@telemetria_router.post(
    "/analyze-telemetry",
    response_model=RespuestaTelemetriaDTO,
    status_code=status.HTTP_200_OK,
    summary="Analizar telemetría de landmarks en tiempo real",
    description="Recibe coordenadas numéricas de articulaciones extraídas por el Telemetry Server (MediaPipe) y computa el análisis cinemático sin almacenar video."
)
def analizar_telemetria(solicitud: SolicitudTelemetriaDTO):
    try:
        caso_de_uso = ProcesarTelemetriaStreamingUseCase()
        resultado = caso_de_uso.ejecutar(
            landmarks=[item.model_dump() for item in solicitud.landmarks],
            articulacion=solicitud.articulacion or "Rodilla Derecha",
            session_id=solicitud.session_id,
            frame_id=solicitud.frame_id
        )
        return resultado
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante el análisis de telemetría: {str(exc)}"
        )
