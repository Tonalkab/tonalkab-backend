from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

# Importaciones de los modelos de Tonalkab
from app.models.maceta import Maceta
from app.models.lectura import LecturaSensores
from app.models.tipo_planta import TipoPlanta
from app.models.conexion import ConexionDispositivo
from app.models.control_riego import ControlRiego
from app.models.configuracion_maceta import ConfiguracionMaceta

# =======================================================
# HERRAMIENTA 1: Ojo y Cerebro (Lectura de Datos)
# =======================================================
def consultar_mis_plantas(id_usuario: int, db: Session):
    macetas = db.query(Maceta).filter(Maceta.id_usuario == id_usuario).all()
    if not macetas:
        return "El usuario aún no tiene macetas registradas."

    datos = []
    for m in macetas:
        planta = db.query(TipoPlanta).filter(TipoPlanta.id_tipo_planta == m.id_tipo_planta).first()
        lectura = db.query(LecturaSensores).filter(LecturaSensores.id_maceta == m.id_maceta).order_by(LecturaSensores.fecha_hora.desc()).first()
        conexion = db.query(ConexionDispositivo).filter(ConexionDispositivo.id_maceta == m.id_maceta).first()
        
        rssi = conexion.rssi if conexion else -100
        
        hace_30_dias = datetime.utcnow() - timedelta(days=30)
        agua_usada_ml = db.query(func.sum(ControlRiego.cantidad_agua_ml)).filter(
            ControlRiego.id_maceta == m.id_maceta,
            ControlRiego.fecha_fin_riego >= hace_30_dias
        ).scalar() or 0.0

        agua_teorica_ml = 4500.0 
        ahorro_ml = max(0, agua_teorica_ml - float(agua_usada_ml))
        dias_conmigo = (datetime.utcnow() - m.fecha_registro).days

        # OJO AQUÍ: Le pasamos el ID_MACETA al bot para que sepa a quién regar
        info = f"--- MACETA: '{m.nombre_maceta}' (ID: {m.id_maceta}) ---\n"
        if planta:
            info += f"Especie: {planta.nombre_planta}\n"
            info += f"Rangos Ideales: Humedad {planta.humedad_suelo_min}%-{planta.humedad_suelo_max}%, Temp {planta.temperatura_min}°C-{planta.temperatura_max}°C\n"
            info += f"Cuidados específicos: {planta.cuidados_generales}\n"
        
        info += f"Días en el sistema: {dias_conmigo} días.\n"
        
        if lectura:
            info += f"Estado Actual: Humedad {lectura.humedad_suelo}%, Temp {lectura.temperatura}°C.\n"
            info += f"Salud IoT: Señal WiFi (RSSI) {rssi} dBm. Batería: {lectura.voltaje_bateria}V.\n"
        else:
            info += "Estado Actual: Sin lecturas de sensores disponibles.\n"
            
        info += f"Métricas Mensuales: Agua usada {agua_usada_ml}ml. Ahorro estimado: {ahorro_ml}ml.\n"
            
        datos.append(info)
    
    return "\n".join(datos)

# =======================================================
# HERRAMIENTA 2: La Mano Físicamente (Escritura / Hardware)
# =======================================================
def forzar_riego_fisico(id_maceta: int, mililitros: float, id_usuario: int, db: Session) -> str:
    """
    Herramienta que la IA usa para activar la bomba de agua del ESP32.
    """
    # 1. Validar que la maceta sea de este usuario
    maceta = db.query(Maceta).filter(Maceta.id_maceta == id_maceta, Maceta.id_usuario == id_usuario).first()
    if not maceta:
        return "Error de seguridad: La maceta no existe o no te pertenece."
    
    # 2. Buscar la configuración activa
    config = db.query(ConfiguracionMaceta).filter(
        ConfiguracionMaceta.id_maceta == id_maceta, 
        ConfiguracionMaceta.activa == True
    ).first()
    
    if not config:
        return "Error: La maceta no tiene una configuración activa para enviar la orden."
        
    try:
        # 3. Dar la orden al ESP32 (Cambia el flag en BD)
        config.modo_operacion = "manual"
        config.dosis_ml_calculada = float(mililitros)
        db.commit()
        return f"Éxito total. He inyectado la orden en la base de datos. El relé de la bomba en la maceta '{maceta.nombre_maceta}' liberará {mililitros}ml en el próximo ciclo de telemetría."
    except Exception as e:
        db.rollback()
        return f"Error en el clúster al intentar enviar la orden: {str(e)}"