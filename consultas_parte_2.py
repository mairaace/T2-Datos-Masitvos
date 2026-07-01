import millenniumdb_driver
import pandas as pd
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import operator

from parametros import TOP_K, API_KEY
from funciones_generales import query_to_df, generar_respuesta_rag

# Recuperación con restricción tipada
def query_partido_tema(partido_objetivo, tema_a_buscar, modelo_e5):
    texto_para_vectorizar = f"query: {tema_a_buscar}"
    vector_tema = modelo_e5.encode_query(texto_para_vectorizar, normalize_embeddings=True)

    query_graphrag = f"""
    MATCH (?i :Intervention)-[:DeliveredBy]->(:Position)-[:Represents]->(?party :PoliticalParty)
    WHERE ?party.name == ?nombre_partido

    MATCH (?i)-[:HasEmbedding]->(?e :Embedding)
    LET ?dist = COSINE_DISTANCE(?vector_q, ?e.value)

    ORDER BY ?dist ASC
    RETURN DISTINCT
        ?i.transcription AS ?texto_intervencion, 
        ?i.context AS ?contexto_intervencion,
        ?party.name AS ?partido_politico,
        ?dist AS ?score_similitud
    LIMIT {TOP_K}
    """

    parametros = {
        "vector_q": vector_tema,
        "nombre_partido": partido_objetivo
    }

    return query_to_df(query_graphrag, parametros)

# Agregación / contraste
def query_comparacion_partidos(tema_a_buscar, modelo_e5):
    texto_para_vectorizar = f"query: {tema_a_buscar}"
    vector_tema = modelo_e5.encode_query(texto_para_vectorizar, normalize_embeddings=True)

    query_contraste = f"""
    MATCH (?party :PoliticalParty)<-[:Represents]-(?pos :Position)<-[:DeliveredBy]-(?i :Intervention)-[:HasEmbedding]->(?emb :Embedding)
    LET ?dist = COSINE_DISTANCE(?q, ?emb.value)
    ORDER BY ?dist ASC
    RETURN DISTINCT
        ?party.name AS ?Partido,
        ?i.transcription AS ?Texto,
        ?i.context AS ?Contexto,
        ?dist AS ?score_similitud
    LIMIT {TOP_K}
    """

    parametros = {
        "q": vector_tema,
    }

    return query_to_df(query_contraste, parametros=parametros)

# Consulta que use un atributo numérico/temporal:
def contexto_filtro_edad(tema_a_buscar, edad, operador_str, modelo_e5):
    texto_para_vectorizar = f"query: {tema_a_buscar}"
    vector_tema = modelo_e5.encode_query(texto_para_vectorizar, normalize_embeddings=True)

    query = """
    MATCH (?person :Person)-[:ServedAs]->(?pos :Position)<-[:DeliveredBy]-(?i :Intervention)
    MATCH (?i)-[:HasEmbedding]->(?emb :Embedding)
    MATCH (?i)-[:HasIntervention]->(?pro :Procedure)
    
    LET ?dist = COSINE_DISTANCE(?q, ?emb.value)
    
    ORDER BY ?dist ASC
    
    RETURN DISTINCT
        ?person.full_name AS ?nombre,
        ?person.birth_date AS ?fecha_nacimiento,
        ?pro.date AS ?fecha_intervencion,
        ?i.transcription AS ?texto,
        ?dist AS ?score_similitud
    LIMIT 50
    """

    parametros = {
        "q": vector_tema
    }

    df = query_to_df(query, parametros)

    df['fecha_nacimiento'] = pd.to_datetime(df['fecha_nacimiento'], errors='coerce')
    df['fecha_intervencion'] = pd.to_datetime(df['fecha_intervencion'], errors='coerce')
    df['edad_al_momento'] = (df['fecha_intervencion'] - df['fecha_nacimiento']).dt.days // 365.25
    df['edad_al_momento'] = df['edad_al_momento'].astype(int)
    df = df.dropna(subset=['edad_al_momento'])
    df = df.drop(columns=["fecha_nacimiento", "fecha_intervencion"])

    ops = {
        '<': operator.lt,
        '<=': operator.le,
        '>': operator.gt,
        '>=': operator.ge,
        '==': operator.eq,
        '!=': operator.ne
    }

    funcion_comparacion = ops[operador_str]
    mascara = funcion_comparacion(df['edad_al_momento'], edad)
    df_filtrado = df[mascara].iloc[:TOP_K].reset_index(drop=True)
    
    return df_filtrado

if __name__ == '__main__':
    cliente = OpenAI(api_key=API_KEY)
    modelo_e5 = SentenceTransformer('intfloat/multilingual-e5-base')

    # -------------------
    tema_a_buscar = "reducción de la jornada laboral a 40 horas"
    partido_objetivo = "Partido Comunista de Chile"
    df_recuperado = query_partido_tema(partido_objetivo, tema_a_buscar, modelo_e5)

    pregunta_llm_1 = f"¿Qué argumentos a favor y en contra realizó el {partido_objetivo} sobre la {tema_a_buscar}?"
    respuesta_1 = generar_respuesta_rag(pregunta_llm_1, df_recuperado, cliente)
    print(respuesta_1)
    # -------------------


    # -------------------
    tema_a_buscar = "reducción de la jornada laboral a 40 horas semanales"
    df_recuperado = query_comparacion_partidos(tema_a_buscar, modelo_e5)

    pregunta_llm_2 = f"Contrasta las posturas de los distintos partidos políticos respecto a la {tema_a_buscar}. ¿En qué puntos coinciden y cuáles son sus principales diferencias?"
    respuesta_2 = generar_respuesta_rag(pregunta_llm_2, df_recuperado, cliente)
    print(respuesta_2)
    # -------------------


    # -------------------
    tema_a_buscar = "reducción de la jornada laboral a 40 horas semanales"
    edad_objetivo = 60
    df_recuperado = contexto_filtro_edad(tema_a_buscar, 60, ">=", modelo_e5)

    pregunta_llm_3 = f"¿Cuál es la postura de los políticos mayores de {edad_objetivo} años respecto a la {tema_a_buscar}?"
    respuesta_edad = generar_respuesta_rag(pregunta_llm_3, df_recuperado, cliente)
    print(respuesta_edad)
    # -------------------




