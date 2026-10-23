from neo4j import GraphDatabase, Query
from neo4j.exceptions import DriverError, Neo4jError

from app.observability import guarded


class Neo4jAdapter:
    def __init__(self, settings):
        self.settings = settings
        self.driver = GraphDatabase.driver(settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password.get_secret_value()),
            connection_timeout=settings.timeout_seconds,
            connection_acquisition_timeout=settings.timeout_seconds,
            max_transaction_retry_time=0)

    @guarded("neo4j", (DriverError, Neo4jError))
    def events(self, match_id, offset, limit):
        with self.driver.session(database=self.settings.neo4j_database) as session:
            exists = session.run(Query("MATCH (p:Partido {id_partido:$id}) RETURN p.id_partido AS id",
                                       timeout=self.settings.timeout_seconds), id=match_id).single()
            if not exists:
                return None
            query = Query("""
                MATCH (p:Partido {id_partido:$id})<-[:OCURRE_EN]-(e:Evento)
                OPTIONAL MATCH (e)-[:PROTAGONIZADO_POR]->(j:Jugador)
                RETURN e.id_evento AS id_evento, e.tipo AS tipo, e.minuto AS minuto,
                       e.descripcion AS descripcion, j.mongo_id AS jugador_id
                ORDER BY e.minuto, e.id_evento, j.mongo_id SKIP $offset LIMIT $limit
            """, timeout=self.settings.timeout_seconds)
            return [record.data() for record in session.run(query, id=match_id, offset=offset, limit=limit+1)]

    @guarded("neo4j", (DriverError, Neo4jError))
    def graph(self):
        labels = ["Partido", "Equipo", "Jugador", "Evento", "Sede"]
        fields = ["id_partido", "mongo_id", "id_evento", "id_sede", "nombre", "apellido",
                  "codigo_fifa", "confederacion", "entrenador", "ranking_fifa", "fecha",
                  "fase", "grupo", "tipo", "minuto", "descripcion", "ciudad", "pais",
                  "capacidad", "fecha_nacimiento", "posicion", "numero_camiseta", "club", "equipo_id"]
        def properties(node):
            return {key: value if isinstance(value, (str, int, float, bool)) or value is None else str(value)
                    for key, value in node.items() if key in fields or key == "rol"}
        with self.driver.session(database=self.settings.neo4j_database) as session:
            with session.begin_transaction(timeout=self.settings.timeout_seconds) as tx:
                total = tx.run("MATCH (n) WHERE any(l IN labels(n) WHERE l IN $labels) RETURN count(n) AS total", labels=labels).single()["total"]
                records = list(tx.run("MATCH (n) WHERE any(l IN labels(n) WHERE l IN $labels) RETURN n ORDER BY elementId(n) LIMIT 5000", labels=labels))
                nodes = [{"id": r["n"].element_id, "tipo": next(l for l in labels if l in r["n"].labels), "propiedades": properties(r["n"])} for r in records]
                ids = [n["id"] for n in nodes]
                relations = list(tx.run("""MATCH (a)-[r]->(b) WHERE elementId(a) IN $ids AND elementId(b) IN $ids
                    AND type(r) IN $types RETURN r, elementId(a) AS origen, elementId(b) AS destino
                    ORDER BY elementId(r) LIMIT 15001""", ids=ids,
                    types=["OCURRE_EN", "PROTAGONIZADO_POR", "PARTICIPA_EN", "SE_JUEGA_EN", "PERTENECE_A"]))
                return {"nodos": nodes, "relaciones": [{"id": r["r"].element_id, "origen": r["origen"], "destino": r["destino"], "tipo": r["r"].type, "propiedades": properties(r["r"])} for r in relations[:15000]],
                        "total_nodos": total, "truncado": total > len(nodes) or len(relations) > 15000}

    @guarded("neo4j", (DriverError, Neo4jError))
    def ping(self):
        with self.driver.session(database=self.settings.neo4j_database) as session:
            session.run(Query("RETURN 1", timeout=self.settings.timeout_seconds)).consume()

    def close(self):
        self.driver.close()
