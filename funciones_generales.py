import millenniumdb_driver
import pandas as pd

from parametros import PROMPT_SISTEMA

def query_to_df(query_string, parametros=None):
    url = 'ws://localhost:1234'
    db_driver = millenniumdb_driver.driver(url)
    session = db_driver.session()

    """Ejecuta una consulta en MDB y devuelve un DataFrame de Pandas"""
    try:
        if parametros:
            resultado = session.run(query_string, parametros)
        else:
            resultado = session.run(query_string)
        
        datos = resultado.data()
        
        if datos:
            return pd.DataFrame(datos)
        else:
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ Error en la consulta: {e}")
        return None
    
    finally:
        db_driver.close()

def generar_respuesta_rag(pregunta_usuario, df_recuperado, cliente):
    """
    Función universal para RAG. Inyecta dinámicamente cualquier columna del DataFrame
    como contexto, manteniendo el System Prompt estrictamente fijo.
    """
    contexto_texto = ""
    
    for index, row in df_recuperado.iterrows():
        contexto_texto += f"--- Documento [{index}] ---\n"
        
        # Iteramos dinámicamente sobre todas las columnas del DataFrame
        for columna, valor in row.items():
            # Ignoramos columnas irrelevantes para el LLM (como el score matemático) o valores vacíos
            if columna not in ['score_similitud', 'distancia'] and pd.notna(valor):
                # Formateamos el nombre de la columna para que se lea natural (ej: partido_politico -> Partido Politico)
                nombre_legible = str(columna).replace("_", " ").title()
                contexto_texto += f"{nombre_legible}: {valor}\n"
                
        contexto_texto += "\n" # Espacio entre documentos

    prompt_usuario = f"CONTEXTO DE LAS INTERVENCIONES:\n{contexto_texto}\n\nPREGUNTA A RESPONDER:\n{pregunta_usuario}"

    respuesta = cliente.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": prompt_usuario}
        ],
        temperature=0.0
    )
    
    return respuesta.choices[0].message.content