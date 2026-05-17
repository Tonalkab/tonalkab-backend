from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LecturaCreate(BaseModel):
    humedad_suelo: float 
    temperatura: float
    humedad_ambiental: float = 0.0
    nivel_luz: int = 0
    nivel_agua: int = 0
    voltaje_bateria: float = 0.0

class LecturaResponse(LecturaCreate):
    id_lectura: int
    id_maceta: int
    fecha_hora: datetime

    class Config:
        from_attributes = True # Permite leer desde el modelo de SQLAlchemy

class RiegoReportCreate(BaseModel):
    humedad_antes: float
    humedad_despues: float
    duracion_bomba_segundos: float
    id_tipo_activacion: int # 1=Manual, 2=Edge (sensor crítico), 3=Timeout, 4=Lluvia
    temperatura_en_momento: float
    luz_en_momento: int

class DeviceConfigResponse(BaseModel):
    # Identificación y Modo
    id_configuracion: int
    modo_operacion: str = "edge_auto" # Puede ser "manual", "edge_auto"
    
    # Umbrales Biológicos (Extraídos de TipoPlanta)
    humedad_suelo_min: float
    humedad_suelo_max: float
    tiempo_min_entre_riegos_dias: int
    
    # Parámetros de Ejecución (El cálculo ML o Reglas de Negocio)
    dosis_ml_calculada: float
    flujo_bomba_ml_por_segundo: float = 15.0 # Constante calibrada del hardware
    
    # Tiempos (Para que el ESP sepa si ya pasó el tiempo de espera)
    horas_desde_ultimo_riego: int
    
    # Parámetro para el Modo Offline del ESP32 (El que agregamos)
    tasa_absorcion_ml_por_porcentaje: float = 5.0