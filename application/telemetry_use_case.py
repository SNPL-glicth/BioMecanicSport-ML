"""
Capa de Aplicación: Caso de uso para la ingesta y análisis cinemático de telemetría por streaming.
Procesa listas de coordenadas de puntos articulares (landmarks) emitidas en tiempo real por el Telemetry Server.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from domain.biomechanics import PuntoArticular, CalculadorBiomecanico


class ProcesarTelemetriaStreamingUseCase:
    """
    Caso de uso para el procesamiento en tiempo real de telemetría de landmarks.
    """

    def __init__(self, calculador: Optional[CalculadorBiomecanico] = None):
        self.calculador = calculador or CalculadorBiomecanico()

    def ejecutar(
        self,
        landmarks: List[Dict[str, Any]],
        articulacion: str = "Rodilla Derecha",
        session_id: Optional[str] = None,
        frame_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calcula la cinemática a partir de los landmarks recibidos:
        - Si hay al menos 3 puntos, utiliza los primeros 3 (o los busca por nombres canónicos: cadera, rodilla, tobillo).
        - Calcula el ángulo articular e identifica riesgo biomecánico.
        """
        if not landmarks or len(landmarks) < 3:
            raise ValueError("Se requieren al menos 3 puntos articulares (landmarks) para calcular un ángulo articular.")

        # Buscar por nombres semánticos de articulaciones o tomar los 3 primeros
        puntos_map = {item.get("name", "").lower(): item for item in landmarks if item.get("name")}

        p_origen_dict = (
            puntos_map.get("hip_right")
            or puntos_map.get("hip")
            or puntos_map.get("cadera")
            or landmarks[0]
        )
        p_vertice_dict = (
            puntos_map.get("knee_right")
            or puntos_map.get("knee")
            or puntos_map.get("rodilla")
            or landmarks[1]
        )
        p_destino_dict = (
            puntos_map.get("ankle_right")
            or puntos_map.get("ankle")
            or puntos_map.get("tobillo")
            or landmarks[2]
        )

        p_origen = PuntoArticular(
            x=float(p_origen_dict.get("x", 0.0)),
            y=float(p_origen_dict.get("y", 0.0)),
            z=float(p_origen_dict.get("z", 0.0)),
            visibilidad=float(p_origen_dict.get("visibility", 1.0))
        )
        p_vertice = PuntoArticular(
            x=float(p_vertice_dict.get("x", 0.0)),
            y=float(p_vertice_dict.get("y", 0.0)),
            z=float(p_vertice_dict.get("z", 0.0)),
            visibilidad=float(p_vertice_dict.get("visibility", 1.0))
        )
        p_destino = PuntoArticular(
            x=float(p_destino_dict.get("x", 0.0)),
            y=float(p_destino_dict.get("y", 0.0)),
            z=float(p_destino_dict.get("z", 0.0)),
            visibilidad=float(p_destino_dict.get("visibility", 1.0))
        )

        # Reglas matemáticas del dominio
        angulo = self.calculador.calcular_angulo_2d(p_origen, p_vertice, p_destino)
        alerta = self.calculador.evaluar_alerta_movimiento(angulo)

        diagnostico = (
            "Alerta: Ángulo articular fuera de rango seguro fisiológico."
            if alerta
            else "Óptimo: Rango cinemático dentro de los estándares biomecánicos."
        )

        return {
            "status": "success",
            "session_id": session_id or "streaming_default",
            "frame_id": frame_id,
            "articulacion": articulacion,
            "angulo_grados": angulo,
            "alerta_riesgo_lesion": alerta,
            "diagnostico_tecnico": diagnostico,
            "puntos_procesados": len(landmarks),
            "timestamp": datetime.now().isoformat()
        }
