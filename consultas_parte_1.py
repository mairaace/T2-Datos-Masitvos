import pandas as pd
from sentence_transformers import SentenceTransformer
from openai import OpenAI

from parametros import TOP_K, API_KEY
from funciones_generales import query_to_df, generar_respuesta_rag

def recuperar_top_k(pregunta_usuario, modelo_e5):
    pregunta_formateada = f"query: {pregunta_usuario}"
    vector_consulta = modelo_e5.encode_query(pregunta_formateada, normalize_embeddings=True)

    query_rag = f"""
    CALL HNSW_TOP_K("idx_congreso", ?vector_q, ?top_k, 100)
    YIELD ?object AS ?nodo_embedding, ?distance AS ?distancia
    MATCH (?intervencion :Intervention)-[:HasEmbedding]->(?nodo_embedding)
    ORDER BY ?distancia ASC
    RETURN 
        ?intervencion.transcription AS ?texto_intervencion, 
        ?intervencion.context AS ?contexto_intervencion, 
        ?distancia AS ?score_similitud
    """

    mis_parametros = {
        "vector_q": vector_consulta,
        "top_k": TOP_K
    }

    return query_to_df(query_rag, mis_parametros)

if __name__ == '__main__':
    cliente = OpenAI(api_key=API_KEY)
    modelo_e5 = SentenceTransformer('intfloat/multilingual-e5-base')

    pregunta_1 = "¿Qué argumentos surgieron sobre la reducción de la jornada laboral a 40 horas?"
    df_recuperado = recuperar_top_k(
        pregunta_usuario=pregunta_1,
        modelo_e5=modelo_e5
    )

    respuesta_final = generar_respuesta_rag(pregunta_1, df_recuperado, cliente)
    print(respuesta_final)