from fastapi import APIRouter, Depends, HTTPException, Security, BackgroundTasks 
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func

from app.db import get_db
from app.models.maceta import Maceta
from app.models.lectura import LecturaSensores
from app.models.tipo_planta import TipoPlanta
from app.models.control_riego import ControlRiego
from app.models.configuracion_maceta import ConfiguracionMaceta
from app.models.predicciones_ml import PrediccionesML
from app.models.alerta import Alerta 
from app.core.security import hash_device_token
from app.schemas.device import LecturaCreate, DeviceConfigResponse, RiegoReportCreate

# Motor de inferencia
from app.ml.inference import generar_prediccion_riego 

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
    background_tasks: BackgroundTasks, 
    current_device: Maceta = Depends(get_current_device),
    db: Session = Depends(get_db)
):
    """
    Recibe los datos del ESP32 y analiza si hubo un evento de lluvia
    utilizando una ventana de tiempo de doble capa para compensar la percolación del suelo.
    Genera alertas en caso de detectar anomalías críticas y dispara la IA.
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

    # 2. ALGORITMO DE DETECCIÓN DE LLUVIA DE DOBLE CAPA
    evento_lluvia_detectado = False
    ahora = datetime.utcnow()
    
    # Definimos nuestras dos ventanas de tiempo
    hace_15_min = ahora - timedelta(minutes=15)
    hace_60_min = ahora - timedelta(minutes=60)

    # Capa 1: Búsqueda del "Valle" a corto plazo (Aguaceros)
    humedad_min_15 = db.query(func.min(LecturaSensores.humedad_suelo)).filter(
        LecturaSensores.id_maceta == current_device.id_maceta,
        LecturaSensores.fecha_hora >= hace_15_min
    ).scalar()

    # Capa 2: Búsqueda del "Valle" a largo plazo (Lloviznas)
    humedad_min_60 = db.query(func.min(LecturaSensores.humedad_suelo)).filter(
        LecturaSensores.id_maceta == current_device.id_maceta,
        LecturaSensores.fecha_hora >= hace_60_min
    ).scalar()

    # Calculamos los incrementos (Deltas)
    delta_15 = float(lectura.humedad_suelo) - float(humedad_min_15) if humedad_min_15 is not None else 0
    delta_60 = float(lectura.humedad_suelo) - float(humedad_min_60) if humedad_min_60 is not None else 0

    es_anomalia = False
    ventana_evaluada = ahora
    humedad_minima_base = 0
    delta_final = 0

    # Lógica de disparo: Evaluamos la capa rápida primero, luego la lenta
    if delta_15 > 8.0:
        es_anomalia = True
        ventana_evaluada = hace_15_min
        humedad_minima_base = float(humedad_min_15)
        delta_final = delta_15
    elif delta_60 > 12.0: 
        es_anomalia = True
        ventana_evaluada = hace_60_min
        humedad_minima_base = float(humedad_min_60)
        delta_final = delta_60

    # Si cruzamos algún umbral, verificamos que no haya sido nuestra propia bomba
    if es_anomalia:
        riego_reciente = db.query(ControlRiego).filter(
            ControlRiego.id_maceta == current_device.id_maceta,
            ControlRiego.fecha_inicio_riego >= ventana_evaluada,
            ControlRiego.resultado_riego == "exitoso",
            ControlRiego.id_tipo_activacion != 4 
        ).first()

        if not riego_reciente:
            evento_lluvia_detectado = True
            tipo_lluvia = "Aguacero" if ventana_evaluada == hace_15_min else "Llovizna"
            print(f"🌧️ ¡{tipo_lluvia} DETECTADA! La humedad subió de {humedad_minima_base}% a {lectura.humedad_suelo}%")
            
            lluvia_ya_registrada = db.query(ControlRiego).filter(
                ControlRiego.id_maceta == current_device.id_maceta,
                ControlRiego.fecha_inicio_riego >= ventana_evaluada,
                ControlRiego.id_tipo_activacion == 4 
            ).first()

            if not lluvia_ya_registrada:
                registro_externo = ControlRiego(
                    id_maceta=current_device.id_maceta,
                    fecha_fin_riego=datetime.utcnow(),
                    humedad_antes=humedad_minima_base,
                    humedad_despues=float(lectura.humedad_suelo),
                    incremento_humedad=delta_final,
                    humedad_objetivo_en_momento=0, 
                    cantidad_agua_ml=0, 
                    duracion_bomba=0,
                    temperatura_en_momento=lectura.temperatura,
                    luz_en_momento=lectura.nivel_luz,
                    id_tipo_activacion=4, 
                    id_estado_registro=1,
                    resultado_riego="exitoso"
                )
                db.add(registro_externo)
                db.commit()

    # ==========================================
    # 3. SISTEMA REACTIVO DE ALERTAS 
    # ==========================================
    config_maceta = obtener_configuracion_edge_dict(current_device, db)

    def disparar_alerta(id_tipo, prioridad, mensaje_alerta):
        alerta_existente = db.query(Alerta).filter(
            Alerta.id_maceta == current_device.id_maceta,
            Alerta.id_tipo_alerta == id_tipo,
            Alerta.id_estado_alerta == 1 
        ).first()
        
        if not alerta_existente:
            nueva_alerta = Alerta(
                id_maceta=current_device.id_maceta,
                id_tipo_alerta=id_tipo,
                mensaje=mensaje_alerta,
                id_estado_alerta=1, 
                id_prioridad_alerta=prioridad
            )
            db.add(nueva_alerta)
            db.commit()

    if float(lectura.humedad_suelo) < config_maceta["humedad_suelo_min"]:
        disparar_alerta(
            id_tipo=1, 
            prioridad=3, 
            mensaje_alerta=f"Humedad crítica: {lectura.humedad_suelo}% (El mínimo vital es {config_maceta['humedad_suelo_min']}%)"
        )

    if 0.0 < float(lectura.voltaje_bateria) < 3.3:
        disparar_alerta(
            id_tipo=2, 
            prioridad=2, 
            mensaje_alerta=f"Batería baja ({lectura.voltaje_bateria}V). Revisa el panel solar de la maceta."
        )

    if int(lectura.nivel_agua) < 10:
        disparar_alerta(
            id_tipo=4, 
            prioridad=3, 
            mensaje_alerta="El depósito de agua está casi vacío. Rellénalo para que el riego autónomo no se detenga."
        )

    # 4. EL GATILLO DE LA IA EN SEGUNDO PLANO
    background_tasks.add_task(generar_prediccion_riego, current_device.id_maceta, db)

    return {
        "status": "success", 
        "id_lectura": nueva_lectura.id_lectura,
        "anomalia_lluvia": evento_lluvia_detectado
    }

# ==========================================
# FUNCION AUXILIAR (Extrae lógica de config para reutilizar)
# ==========================================
def obtener_configuracion_edge_dict(current_device: Maceta, db: Session):
    planta = db.query(TipoPlanta).filter(TipoPlanta.id_tipo_planta == current_device.id_tipo_planta).first()
    config_activa = db.query(ConfiguracionMaceta).filter(
        ConfiguracionMaceta.id_maceta == current_device.id_maceta,
        ConfiguracionMaceta.activa == True
    ).first()

    hum_min = float(config_activa.humedad_suelo_min) if config_activa else (float(planta.humedad_suelo_min) if planta else 0)
    hum_max = float(config_activa.humedad_suelo_max) if config_activa else (float(planta.humedad_suelo_max) if planta else 0)
    dias_riego = config_activa.tiempo_min_entre_riegos_dias if config_activa else (planta.tiempo_min_entre_riegos_dias if planta else 1)
    modo = config_activa.modo_operacion if config_activa else "edge_auto"
    dosis = float(config_activa.dosis_ml_calculada) if config_activa and config_activa.dosis_ml_calculada else 0.0

    return {
        "humedad_suelo_min": hum_min,
        "humedad_suelo_max": hum_max,
        "tiempo_min_entre_riegos_dias": dias_riego,
        "modo_operacion": modo,
        "dosis_ml_calculada": dosis
    }

# ==========================================
# ENDPOINT: Obtención de Configuración (Edge)
# ==========================================
@router.get("/config", response_model=DeviceConfigResponse)
def obtener_configuracion_edge(
    current_device: Maceta = Depends(get_current_device),
    db: Session = Depends(get_db)
):
    """
    Entrega los umbrales operativos y la dosis de riego al ESP32.
    Calcula además la tasa de absorción histórica para que el dispositivo opere offline.
    """
    config_basica = obtener_configuracion_edge_dict(current_device, db)
    
    # Obtener ID de configuración activa
    config_activa = db.query(ConfiguracionMaceta).filter(
        ConfiguracionMaceta.id_maceta == current_device.id_maceta,
        ConfiguracionMaceta.activa == True
    ).first()

    # 3. Calcular horas inactivo
    ultimo_riego = db.query(ControlRiego).filter(
        ControlRiego.id_maceta == current_device.id_maceta,
        ControlRiego.resultado_riego == "exitoso" 
    ).order_by(ControlRiego.fecha_inicio_riego.desc()).first()
    
    horas_inactivo = 0
    if ultimo_riego:
        diferencia = datetime.utcnow() - ultimo_riego.fecha_inicio_riego
        horas_inactivo = int(diferencia.total_seconds() / 3600)

    # 4. Inyección de Machine Learning (Dosis Dinámica)
    dosis_calculada = config_basica["dosis_ml_calculada"]
    
    if dosis_calculada == 0: # Si no hay orden manual, checamos ML
        prediccion_dosis = db.query(PrediccionesML).filter(
            PrediccionesML.id_maceta == current_device.id_maceta,
            PrediccionesML.tipo_prediccion == "dosis_riego"
        ).order_by(PrediccionesML.fecha_generacion.desc()).first()
        
        if prediccion_dosis and prediccion_dosis.confianza_modelo > 80.0:
            dosis_calculada = float(prediccion_dosis.valor_predicho)

    # --- NUEVA LÓGICA: CALCULAR TASA DE ABSORCIÓN HISTÓRICA PARA EL ESP32 ---
    ultimos_riegos_tasa = db.query(ControlRiego).filter(
        ControlRiego.id_maceta == current_device.id_maceta,
        ControlRiego.incremento_humedad > 0
    ).order_by(ControlRiego.fecha_fin_riego.desc()).limit(5).all()

    tasa_esp32 = 5.0  # Valor por defecto si no hay historial aún (Cold Start)
    if ultimos_riegos_tasa:
        tasas = [float(r.cantidad_agua_ml) / float(r.incremento_humedad) for r in ultimos_riegos_tasa]
        tasa_esp32 = sum(tasas) / len(tasas)

    return {
        "id_configuracion": config_activa.id_configuracion if config_activa else 0,
        "modo_operacion": config_basica["modo_operacion"],
        "humedad_suelo_min": config_basica["humedad_suelo_min"],
        "humedad_suelo_max": config_basica["humedad_suelo_max"],
        "tiempo_min_entre_riegos_dias": config_basica["tiempo_min_entre_riegos_dias"],
        "dosis_ml_calculada": dosis_calculada,
        "flujo_bomba_ml_por_segundo": 27.77, 
        "horas_desde_ultimo_riego": horas_inactivo,
        "tasa_absorcion_ml_por_porcentaje": round(tasa_esp32, 2)
    }

# ==========================================
# ENDPOINT: Reporte de Riego (Gatillo de Reset)
# ==========================================
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
    flujo_por_segundo = 15.0 
    cantidad_agua_usada = reporte.duracion_bomba_segundos * flujo_por_segundo
    
    config_dict = obtener_configuracion_edge_dict(current_device, db)

    # 2. Guardamos la transacción en la BD
    nuevo_riego = ControlRiego(
        id_maceta=current_device.id_maceta,
        fecha_fin_riego=datetime.utcnow(),
        humedad_antes=reporte.humedad_antes,
        humedad_despues=reporte.humedad_despues,
        incremento_humedad=incremento,
        humedad_objetivo_en_momento=config_dict["humedad_suelo_max"], 
        cantidad_agua_ml=cantidad_agua_usada,
        duracion_bomba=reporte.duracion_bomba_segundos,
        temperatura_en_momento=reporte.temperatura_en_momento,
        luz_en_momento=reporte.luz_en_momento,
        id_tipo_activacion=reporte.id_tipo_activacion,
        id_estado_registro=1, 
        resultado_riego="exitoso"
    )
    db.add(nuevo_riego)

    # -------------------------------------------------------------------
    # 3. ¡EL PARCHE CRÍTICO! Borrar la orden para evitar bucle infinito
    # -------------------------------------------------------------------
    config_obj = db.query(ConfiguracionMaceta).filter(
        ConfiguracionMaceta.id_maceta == current_device.id_maceta,
        ConfiguracionMaceta.activa == True
    ).first()

    if config_obj and config_obj.dosis_ml_calculada > 0:
        config_obj.dosis_ml_calculada = 0
        config_obj.modo_operacion = "edge_auto"
    
    db.commit()
    db.refresh(nuevo_riego)

    return {"status": "success", "id_riego": nuevo_riego.id_riego, "agua_ml": cantidad_agua_usada}