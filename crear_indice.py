import millenniumdb_driver

# Conectar al servidor local de Docker
url = 'ws://localhost:1234'
db_driver = millenniumdb_driver.driver(url)
session = db_driver.session()

query_indice = """
CREATE HNSW INDEX "idx_congreso" WITH {
    "property"      = "value",
    "dimension"     = 768,
    "maxCandidates" = 64,
    "maxEdges"      = 16,
    "metric"        = "cosineDistance"
}
"""

try:
    # Ejecutar la consulta
    session.run(query_indice)
    print("✅ ¡Índice 'idx_congreso' creado con éxito!")
except Exception as e:
    print(f"❌ Ocurrió un error al crear el índice: {e}")
finally:
    db_driver.close()