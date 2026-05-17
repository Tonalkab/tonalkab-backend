import joblib
import pandas as pd
from sqlalchemy.orm import Session
from app.models.lectura import LecturaSensores
from app.models.predicciones_ml import PrediccionesML
from app.models.configuracion_maceta import ConfiguracionMaceta
from app.models.tipo_planta import TipoPlanta
from app.models.maceta import Maceta
from app.models.control_riego import ControlRiego # <-- IMPORTANTE: Agregar este modelo

# Cargamos el NUEVO modelo v2
model_path = "app/ml/modelo_riego_tonalkab_v2.pkl"
modelo_ia = joblib.load(model_path)

def generar_prediccion_riego(id_maceta: int, db: Session):
    # 1. Obtener la lectura más reciente
    lectura = db.query(LecturaSensores).filter(
        LecturaSensores.id_maceta == id_maceta
    ).order_by(LecturaSensores.fecha_hora.desc()).first()
    
    if not lectura:
        return 0.0

    # 2. Obtener el objetivo (configuración manual o de la planta)
    config = db.query(ConfiguracionMaceta).filter(
        ConfiguracionMaceta.id_maceta == id_maceta, 
        ConfiguracionMaceta.activa == True
    ).first()
    
    if not config:
        maceta = db.query(Maceta).filter(Maceta.id_maceta == id_maceta).first()
        planta = db.query(TipoPlanta).filter(TipoPlanta.id_tipo_planta == maceta.id_tipo_planta).first()
        hum_objetivo = float(planta.humedad_suelo_max)
    else:
        hum_objetivo = float(config.humedad_suelo_max)

    # 3. Calcular el Delta
    delta_necesario = hum_objetivo - float(lectura.humedad_suelo)
    if delta_necesario <= 0:
        return 0.0

    # --- NUEVA LÓGICA: Calcular Tasa Histórica (Últimos 5 riegos) ---
    ultimos_riegos = db.query(ControlRiego).filter(
        ControlRiego.id_maceta == id_maceta,
        ControlRiego.incremento_humedad > 0 # Solo riegos que sí subieron la humedad
    ).order_by(ControlRiego.fecha_fin_riego.desc()).limit(5).all()

    if ultimos_riegos:
        tasas = [float(riego.cantidad_agua_ml) / float(riego.incremento_humedad) for riego in ultimos_riegos]
        tasa_historica = sum(tasas) / len(tasas)
    else:
        tasa_historica = 5.0 # Cold Start: Asumimos 5 ml por cada 1% de humedad si es maceta nueva

    # 4. Preparar datos para Scikit-Learn (Ahora con 5 variables)
    input_data = pd.DataFrame({
        'humedad_antes': [float(lectura.humedad_suelo)],
        'incremento_humedad': [delta_necesario],
        'temperatura_en_momento': [float(lectura.temperatura)],
        'luz_en_momento': [lectura.nivel_luz],
        'tasa_absorcion_historica': [tasa_historica] # <-- El historial inyectado
    })

    # 5. Predecir
    ml_predichos = modelo_ia.predict(input_data)[0]

    return float(ml_predichos)