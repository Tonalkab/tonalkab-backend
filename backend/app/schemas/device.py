from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LecturaCreate(BaseModel):
    humedad_suelo: float = Field(..., ge=0.0, le=100.0, description="Porcentaje de humedad en suelo (0-100%)")
    temperatura: float = Field(..., ge=-30.0, le=80.0, description="Temperatura en grados Celsius (-30 a 80°C)")
    humedad_ambiental: float = Field(0.0, ge=0.0, le=100.0, description="Porcentaje de humedad ambiental (0-100%)")
    nivel_luz: int = Field(0, ge=0, le=100000, description="Nivel de luz / Lux / ADC")
    nivel_agua: int = Field(0, ge=0, le=100, description="Porcentaje de nivel de agua en tanque (0-100%)")
    voltaje_bateria: float = Field(0.0, ge=0.0, le=15.0, description="Voltaje de la batería en Volts")

class LecturaResponse(LecturaCreate):
    id_lectura: int
    id_maceta: int
    fecha_hora: datetime

    class Config:
        from_attributes = True # Permite leer desde el modelo de SQLAlchemy

class RiegoReportCreate(BaseModel):
    humedad_antes: float = Field(..., ge=0.0, le=100.0)
    humedad_despues: float = Field(..., ge=0.0, le=100.0)
    duracion_bomba_segundos: float = Field(..., ge=0.0, le=300.0)
    id_tipo_activacion: int = Field(..., ge=1, le=4, description="1=Manual, 2=Edge, 3=Timeout, 4=Lluvia")
    temperatura_en_momento: float = Field(..., ge=-30.0, le=80.0)
    luz_en_momento: int = Field(..., ge=0)

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