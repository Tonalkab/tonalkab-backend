from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db import get_db
from app.models.maceta import Maceta
from app.models.lectura import LecturaSensores
from app.models.tipo_planta import TipoPlanta
from app.models.control_riego import ControlRiego
from app.models.configuracion_maceta import ConfiguracionMaceta
from app.models.predicciones_ml import PrediccionesML

from app.core.security import hash_device_token
# IMPORTANTE: Asegúrate de añadir RiegoReportCreate a tu app/schemas/device.py como hicimos en el paso anterior
from app.schemas.device import LecturaCreate, DeviceConfigResponse, RiegoReportCreate

from sqlalchemy import func

# Configuración del Router y Seguridad
router = APIRouter(prefix="/devices", tags=["Dispositivos IoT (ESP32)"])

# Definimos el header que el ESP32 debe enviar
api_key_header = APIKeyHeader(name="X-Device-Token", auto_error=True)

# ==========================================
# DEPENDENCIA: Autenticación del Dispositivo
# ==========================================
def get_current_device(
    token: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """
    Valida el token plano enviado por el hardware.
    """
    token_hash = hash_device_token(token)
    maceta = db.query(Maceta).filter(Maceta.token_hash == token_hash).first()

    if not maceta:
        raise HTTPException(
            status_code=401, 
            detail="Token de dispositivo inválido o maceta no encontrada"
        )

    return maceta

# ==========================================
# ENDPOINT: Verificación de Conexión (Auth)
# ==========================================
@router.post("/auth")
def auth_device(current_device: Maceta = Depends(get_current_device)):
    """
    Endpoint para que el ESP32 valide su llave al arrancar.
    """
    return {
        "message": "Dispositivo autenticado correctamente",
        "id_maceta": current_device.id_maceta,
        "nombre": current_device.nombre_maceta
    }

# ==========================================
# ENDPOINT: Recepción de Lecturas Sensores
# ==========================================


@router.post("/lecturas")
def receive_lecturas(
    lectura: LecturaCreate,
    current_device: Maceta = Depends(get_current_device),
    db: Session = Depends(get_db)
):
    """
    Recibe los datos del ESP32 y analiza si hubo un evento de lluvia
    utilizando una ventana de tiempo para compensar la percolación del suelo.
    """
    # 1. GUARDADO NORMAL DE LA LECTURA ACTUAL
    nueva_lectura = LecturaSensores(
        id_maceta=current_device.id_maceta,
        humedad_suelo=lectura.humedad_suelo,
        temperatura=lectura.temperatura,
        humedad_ambiental=lectura.humedad_ambiental,
        nivel_luz=lectura.nivel_luz,
        nivel_agua=lectura.nivel_agua,
        voltaje_bateria=lectura.voltaje_bateria,
    )
    db.add(nueva_lectura)
    db.commit()
    db.refresh(nueva_lectura)

    # 2. ALGORITMO DE DETECCIÓN DE LLUVIA (Ventana de 15 Minutos)
    evento_lluvia_detectado = False
    
    # Definimos nuestra ventana de tiempo hacia el pasado
    hace_15_min = datetime.utcnow() - timedelta(minutes=15)

    # Buscamos la humedad MÁS BAJA registrada en esos 15 minutos (el "Valle")
    humedad_minima_reciente = db.query(func.min(LecturaSensores.humedad_suelo)).filter(
        LecturaSensores.id_maceta == current_device.id_maceta,
        LecturaSensores.fecha_hora >= hace_15_min
    ).scalar()

    if humedad_minima_reciente is not None:
        # Calculamos la diferencia desde el punto más bajo hasta la lectura actual (el "Pico")
        delta_humedad = float(lectura.humedad_suelo) - float(humedad_minima_reciente)
        
        # UMBRAL: Si desde el punto más bajo hasta ahora subió más del 8%
        if delta_humedad > 8.0: 
            
            # Verificamos si la BOMBA se prendió en esa misma ventana de tiempo
            riego_reciente = db.query(ControlRiego).filter(
                ControlRiego.id_maceta == current_device.id_maceta,
                ControlRiego.fecha_inicio_riego >= hace_15_min,
                ControlRiego.resultado_riego == "exitoso"
            ).first()

            # Si subió gradualmente (o de golpe) PERO la bomba no fue la responsable... ¡Llovió!
            if not riego_reciente:
                evento_lluvia_detectado = True
                print(f"🌧️ ¡LLUVIA DETECTADA! La humedad subió de {humedad_minima_reciente}% a {lectura.humedad_suelo}%")
                
                # Para no generar un registro nuevo por cada lectura mientras siga subiendo la humedad,
                # buscamos si ya registramos una lluvia en los últimos 15 minutos.
                lluvia_ya_registrada = db.query(ControlRiego).filter(
                    ControlRiego.id_maceta == current_device.id_maceta,
                    ControlRiego.fecha_inicio_riego >= hace_15_min,
                    ControlRiego.id_tipo_activacion == 4 # 4 = Lluvia
                ).first()

                if not lluvia_ya_registrada:
                    registro_externo = ControlRiego(
                        id_maceta=current_device.id_maceta,
                        fecha_fin_riego=datetime.utcnow(),
                        humedad_antes=float(humedad_minima_reciente),
                        humedad_despues=float(lectura.humedad_suelo),
                        incremento_humedad=delta_humedad,
                        humedad_objetivo_en_momento=0, 
                        cantidad_agua_ml=0, 
                        duracion_bomba=0,
                        temperatura_en_momento=lectura.temperatura,
                        luz_en_momento=lectura.nivel_luz,
                        id_tipo_activacion=4, # 4 = Lluvia / Riego Externo
                        id_estado_registro=1,
                        resultado_riego="exitoso"
                    )
                    db.add(registro_externo)
                    db.commit()

    return {
        "status": "success", 
        "id_lectura": nueva_lectura.id_lectura,
        "anomalia_lluvia": evento_lluvia_detectado
    }

@router.get("/config", response_model=DeviceConfigResponse)
def obtener_configuracion_edge(
    current_device: Maceta = Depends(get_current_device),
    db: Session = Depends(get_db)
):
    """
    Entrega los umbrales operativos y la dosis de riego al ESP32.
    Prioriza configuraciones manuales del usuario, cayendo por defecto a la biología de la planta.
    """
    # 1. Obtener datos biológicos base de la planta
    planta = db.query(TipoPlanta).filter(TipoPlanta.id_tipo_planta == current_device.id_tipo_planta).first()
    if not planta:
        raise HTTPException(status_code=404, detail="Tipo de planta no asociado a la maceta.")

    # 2. Buscar si hay una configuración personalizada activa por el usuario
    config_activa = db.query(ConfiguracionMaceta).filter(
        ConfiguracionMaceta.id_maceta == current_device.id_maceta,
        ConfiguracionMaceta.activa == True
    ).first()

    # Combinamos lógicamente (La configuración del usuario sobreescribe la biología por defecto)
    hum_min = float(config_activa.humedad_suelo_min) if config_activa else float(planta.humedad_suelo_min)
    hum_max = float(config_activa.humedad_suelo_max) if config_activa else float(planta.humedad_suelo_max)
    dias_riego = config_activa.tiempo_min_entre_riegos_dias if config_activa else planta.tiempo_min_entre_riegos_dias
    modo = config_activa.modo_operacion if config_activa else "edge_auto"

    # 3. Calcular horas inactivo (Crucial para el Riego por Tiempo de Espera)
    ultimo_riego = db.query(ControlRiego).filter(
        ControlRiego.id_maceta == current_device.id_maceta,
        ControlRiego.resultado_riego == "exitoso" # Solo contamos riegos que sí se completaron
    ).order_by(ControlRiego.fecha_inicio_riego.desc()).first()
    
    horas_inactivo = 0
    if ultimo_riego:
        diferencia = datetime.utcnow() - ultimo_riego.fecha_inicio_riego
        horas_inactivo = int(diferencia.total_seconds() / 3600)

    # 4. Inyección de Machine Learning (Dosis Dinámica)
    # Buscamos la última predicción generada en background para esta maceta
    dosis_calculada = 200.0 # Base segura por defecto (ml)
    
    prediccion_dosis = db.query(PrediccionesML).filter(
        PrediccionesML.id_maceta == current_device.id_maceta,
        PrediccionesML.tipo_prediccion == "dosis_riego"
    ).order_by(PrediccionesML.fecha_generacion.desc()).first()
    
    if prediccion_dosis and prediccion_dosis.confianza_modelo > 80.0:
        dosis_calculada = float(prediccion_dosis.valor_predicho)

    return {
        "id_configuracion": config_activa.id_configuracion if config_activa else 0,
        "modo_operacion": modo,
        "humedad_suelo_min": hum_min,
        "humedad_suelo_max": hum_max,
        "tiempo_min_entre_riegos_dias": dias_riego,
        "dosis_ml_calculada": dosis_calculada,
        "flujo_bomba_ml_por_segundo": 15.0, # Ajusta esto midiendo cuánto escupe tu bomba real en 1 seg
        "horas_desde_ultimo_riego": horas_inactivo
    }



@router.post("/riego")
def reportar_riego_ejecutado(
    reporte: RiegoReportCreate,
    current_device: Maceta = Depends(get_current_device),
    db: Session = Depends(get_db)
):
    """
    El ESP32 informa que acaba de completar un ciclo de riego físico.
    """
    # 1. Calculamos metadatos en el servidor
    incremento = reporte.humedad_despues - reporte.humedad_antes
    
    # Asumimos que la bomba tiene un flujo constante (puedes mover esto a una variable ENV o de catálogo)
    flujo_por_segundo = 15.0 
    cantidad_agua_usada = reporte.duracion_bomba_segundos * flujo_por_segundo

    # Obtenemos el objetivo dinámico del momento para saber si nos pasamos o faltó
    config = obtener_configuracion_edge(current_device, db) # Reutilizamos la lógica
    
    # 2. Guardamos la transacción en la BD
    nuevo_riego = ControlRiego(
        id_maceta=current_device.id_maceta,
        fecha_fin_riego=datetime.utcnow(),
        humedad_antes=reporte.humedad_antes,
        humedad_despues=reporte.humedad_despues,
        incremento_humedad=incremento,
        humedad_objetivo_en_momento=config["humedad_suelo_max"], 
        cantidad_agua_ml=cantidad_agua_usada,
        duracion_bomba=reporte.duracion_bomba_segundos,
        temperatura_en_momento=reporte.temperatura_en_momento,
        luz_en_momento=reporte.luz_en_momento,
        id_tipo_activacion=reporte.id_tipo_activacion,
        id_estado_registro=1, # 1 = exitoso
        resultado_riego="exitoso"
    )

    db.add(nuevo_riego)
    db.commit()
    db.refresh(nuevo_riego)

    # Nota: Aquí podríamos disparar la lógica de "Lluvia" si vemos que la bomba duró 0s 
    # pero la humedad subió, o manejarlo en el endpoint de lecturas generales.

    return {"status": "success", "id_riego": nuevo_riego.id_riego, "agua_ml": cantidad_agua_usada}