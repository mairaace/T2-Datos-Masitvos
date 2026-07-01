# MQL en MillenniumDB — Hoja de referencia rápida

- Quad Model
- Variables con prefijo `?`
- Aristas **siempre dirigidas**.

## 1. Estructura de una consulta

Toda consulta empieza con `MATCH` y termina con `RETURN`. Entre medio van otros statements; los comentarios usan `//`. 

```SQL
// edad y nombre de quienes conocen a John
MATCH (?x :Person)-[:Knows]->(John)
WHERE ?x.age >= 60 AND ?x.age <= 70
ORDER BY ?x.name DESC, ?x.age ASC
RETURN ?x.age, ?x.name
LIMIT 1000 
```

Orden general: `MATCH` / `WHERE` / `LET` / `CALL` (uno o más) → `GROUP BY` → `HAVING` → `ORDER BY` → `RETURN`. 

## 2. Objetos y variables

Un nodo puede referirse a un objeto fijo (por id) o ligarse a una variable ?x. 

|**Tipo**|**Ejemplo**|
|---|---|
|NamedNode|`(Juan_Perez)`|
|Nodo anónimo|`(_a123)`|
|Arista (por id)|`(_e123)`|
|String|"texto"|`"texto"`|
|Booleano|`true` `false`|
|Entero/Float|`123` `3.14`|
|Variable|`?x`|


## 3. Patrón de nodo

```SQL
()                      // cualquier objeto
(Juan_Perez)            // objeto fijo por id
(?x)                    // variable 
(:Diputado)             // por etiqueta
(:Diputado :Persona)    // varias etiquetas
(?x :Diputado) 
(?x {edad: 42})         // por propiedad
(?x :Diputado {region: "Maule"}) 
```

Un nodo admite _varias_ etiquetas; las propiedades van al final. 

## 4. Patrón de arista (dirigida) 

Las aristas siempre llevan dirección y a lo sumo **un** tipo. 

```SQL
(?x)-[?e]->(?y)         // variable de arista
(?x)-[_e123]->(?y)      // arista fija por id
(?x)-[:Vota]->(?y)      // tipo fijo
(?x)-[?e :Vota]->(?y)   // variable + tipo
(?x)-[:?t]->(?y)        // variable de tipo
(?x)-[{peso: 3}]->(?y)  // con propiedades
(?y)<-[:Vota]-(?z)      // sentido inverso
```

## 5. Caminos (RPQ)

Conectan dos nodos por una _expresión regular de caminos_ sobre tipos. Delimitadores: `=[ ... ]=>` (derecha) y `<=[ ... ]=` (izquierda). 

- `^t`: Tipo `t` en sentido inverso
- `t*`: 0 o más repeticiones
- `t+`: 1 o más repeticiones 
- `t?`: 0 o 1 repetición 
- `t1/t2`: Secuencia (t1 luego t2)
- `t1|t2`: Alternativa (t1 o t2)
- `{m,n}`: Entre m y n repeticiones 

```SQL
(?x)=[:Conoce+]=>(?y) 
(Foo)<=[ALL ?p :Conoce+]=(?z) 
(Foo)=[ANY ?p :Vota+/:De?]=>(Bar)
```

Semántica opcional antes del tipo: `ANY` (def.) o `ALL`; modos `SHORTEST`, `SIMPLE`, `ACYCLIC`, `TRAILS`, `WALKS`. Variable de camino `?p` opcional. 

## 6. Filtros dentro de {}

Dentro de las llaves de un nodo/arista se filtra directamente: 

- `{k: v}`: igualdad exacta
- `{k op v}`: `==` `!=` `<` `>` `<=` `>=` 
- `{k IS [NOT] T}`: T = NULL, STRING, BOOL, INTEGER, FLOAT 
- `{k: date("...")}`: valor con tipo de dato 

```SQL
(?p :Diputado {edad > 30})
(?p :Diputado {region: "Maule", 
               activo IS NOT NULL}) 
```

## 7. WHERE y operadores

`WHERE` filtra con una expresión que debe evaluar a verdadero. 

```SQL
MATCH (?x :Diputado)
WHERE ?x.edad >= 30 AND ?x.edad <= 80
      AND ?x.region != "Maule"
RETURN ?x 
```

- Lógicos: `AND` `OR` `NOT`
- Comparación: `==` `!=` `<` `>` `<=` `>=`
- Aritméticos: `+` `-` `*` `/` `%`
- Tipo: `?x.k IS NOT NULL`
- Igualdad de objeto: `?x == (Foo)`

Ojo: la igualdad es `==` (no `=`). El acceso a propiedad es `?x.clave`. 

## 8. Filtros con expresiones regulares

`REGEX(texto, "patrón", "flags")` es verdadero si _texto_ calza con la regex. El 3er argumento (flags) es opcional. 

```SQL
MATCH (?p :Proyecto)
WHERE REGEX (?p.titulo, "educaci[oó]n", "i") 
RETURN ?p 
```

- `"i"` = _case insensitive_ (ignora mayús/minús).
- Patrón sobre la propiedad: `"ˆLey"` (empieza), `"reforma$"` (termina), `"salud|salario"` (alternativa). 

## 9. Statements principales

#### LET (variables derivadas)

```SQL
MATCH (?a :Diputado)
LET ?decada = ?a.edad / 10
RETURN ?a.nombre, ?decada 
```

#### RETURN: DISTINCT, *, alias

```SQL
RETURN *
RETURN DISTINCT ?x
RETURN ?x.nombre AS ?nombre, ?x.edad 
```

#### ORDER BY, LIMIT, OFFSET 

```SQL
MATCH (?a :Diputado)
ORDER BY ?a.edad DESC
RETURN ?a.nombre, ?a.edad
OFFSET 3
LIMIT 10 
```

#### OPTIONAL (unión opcional, tipo left-join) 

```SQL
MATCH (?x :Diputado)
OPTIONAL { (?x)-[:Preside] -> (?c) }
RETURN ?x.nombre, ?c 
```

## 10. Funciones y agregación 

#### Agregación: GROUP BY / HAVING 

```SQL
MATCH (?a :Diputado)
GROUP BY ?a.region
HAVING COUNT(*) > 5
RETURN ?a.region, COUNT (*) AS ?n 
```

Agregados: `COUNT` (con `DISTINCT`), `SUM` `AVG` `MIN` `MAX`.

#### Funciones útiles
- `REGEX(s,p,f?)`: coincidencia regex
- `EDIT_DISTANCE(a,b)`: distancia de edición
- `STR(x)`: a string
- `LABELS(x)`: etiquetas del nodo
- `TYPE(e)`: tipo de la arista
- `PROPERTIES(x)`: propiedades
- `NORMALIZE(v)`: normaliza vector 

## 11. Similitud de vectores

Los _embeddings_ se guardan como tensores 1-D en una propiedad (p.ej. embedding). Métricas: `COSINE_DISTANCE`, `COSINE_SIMILARITY`, `EUCLIDEAN_DISTANCE`, `MANHATTAN_DISTANCE`

#### Fuerza bruta (exacto)

```SQL
LET ?fijo = nodoConsulta
MATCH (?d :Intervencion)
LET ?dist = COSINE_DISTANCE(?fijo.embedding, ?d.embedding)
ORDER BY ?dist
RETURN ?d, ?dist
LIMIT 100
```

Menor distancia coseno = más similar

#### Aproximado con índice HNSW (rápido a gran escala)

```SQL
CALL HNSW_TOP_K("mi_indice", ?fijo.embedding, 100, 1000)
YIELD ?object AS ?similar, ?dist
RETURN ?similar, ?dist
```

Argumentos: `(indice, vector, k, ef)`. El índice se crea aparte:

```SQL
CREATE HNSW INDEX "mi_indice" WITH {
    "property" = "value",
    "dimension" = 768,
    "maxCandidates" = 16,
    "maxEdges" = 8,
    "metric" = "cosineDistance"
}
```

## 12. Recetas típicas para GraphRAG

#### Top-k denso sobre intervenciones 

```SQL
LET ?q = consultaEmbedding
MATCH (?i :Intervencion)
LET ?s = COSINE_DISTANCE(?q, ?i.embedding)
ORDER BY ?s
RETURN ?i.texto, ?s
LIMIT 10 
```

#### Filtrar por metadato y luego rankear 

```SQL
MATCH (?i :Intervencion)-[:De]->(?a :Diputado)
WHERE ?a.partido == "PartidoX"
LET ?s = COSINE_DISTANCE(?q, ?i.embedding)
ORDER BY ?s
RETURN ?i.texto, ?a.nombre, ?s
LIMIT 10 
```

#### Expansión por grafo (vecinos del resultado) 

```SQL
MATCH (?i :Intervencion)-[:Menciona]->(?p :Proyecto)
WHERE REGEX (?p.titulo, "pension", "i")
RETURN DISTINCT ?p.titulo 
```