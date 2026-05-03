import joblib
import pandas as pd
from sqlalchemy.orm import Session
from app.models.lectura import LecturaSensores
from app.models.predicciones_ml import PrediccionesML
from app.models.configuracion_maceta import ConfiguracionMaceta
from app.models.tipo_planta import TipoPlanta
from app.models.maceta import Maceta

# Cargamos el cerebro de la IA al iniciar el servidor
model_path = "app/ml/modelo_riego_tonalkab.pkl"
modelo_ia = joblib.load(model_path)

def generar_prediccion_riego(id_maceta: int, db: Session):
    # 1. Obtener la lectura más reciente de esta maceta específica
    lectura = db.query(LecturaSensores).filter(
        LecturaSensores.id_maceta == id_maceta
    ).order_by(LecturaSensores.fecha_hora.desc()).first()
    
    if not lectura:
        return None

    # 2. Obtener el objetivo (de la configuración del usuario o de la planta)
    config = db.query(ConfiguracionMaceta).filter(
        ConfiguracionMaceta.id_maceta == id_maceta, 
        ConfiguracionMaceta.activa == True
    ).first()
    
    if not config:
        # Fallback a la biología de la planta si no hay config manual
        maceta = db.query(Maceta).filter(Maceta.id_maceta == id_maceta).first()
        planta = db.query(TipoPlanta).filter(TipoPlanta.id_tipo_planta == maceta.id_tipo_planta).first()
        hum_objetivo = float(planta.humedad_suelo_max)
    else:
        hum_objetivo = float(config.humedad_suelo_max)

    # 3. Preparar los datos para la IA
    # Incremento necesario = Objetivo - Actual
    delta_necesario = hum_objetivo - float(lectura.humedad_suelo)
    
    # Si ya está lo suficientemente húmeda, no predecimos riego
    if delta_necesario <= 0:
        return 0.0

    input_data = pd.DataFrame({
        'humedad_antes': [float(lectura.humedad_suelo)],
        'incremento_humedad': [delta_necesario],
        'temperatura_en_momento': [float(lectura.temperatura)],
        'luz_en_momento': [lectura.nivel_luz]
    })

    # 4. Realizar la predicción
    ml_predichos = modelo_ia.predict(input_data)[0]

    # 5. Guardar en la tabla de predicciones para que el ESP32 la recoja
    nueva_prediccion = PrediccionesML(
        id_maceta=id_maceta,
        id_lectura_base=lectura.id_lectura,
        tipo_prediccion="dosis_riego",
        valor_predicho=ml_predichos,
        unidad_medida="ml",
        confianza_modelo=95.0, # Basado en tu R2 de 0.96
        version_modelo="v1.0-simulado",
        periodo_pronostico=0
    )
    
    db.add(nueva_prediccion)
    db.commit()
    
    return ml_predichos