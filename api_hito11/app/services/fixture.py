from datetime import timezone
from time import perf_counter

from app.errors import ApiError, missing
from app.services.cursors import CursorCodec


class FixtureService:
    def __init__(self, adapters, settings):
        self.adapters = adapters
        self.cursors = CursorCodec(settings.cursor_secret.get_secret_value())

    def team(self, code):
        result = self.adapters["mongodb"].get_team(code)
        if result is None:
            raise missing("el equipo")
        return result

    def teams(self, after, limit, confederation):
        rows = self.adapters["mongodb"].list_teams(after, limit, confederation)
        return {"items": rows[:limit], "siguiente_codigo": rows[limit-1]["codigo_fifa"] if len(rows) > limit else None}

    def events(self, match_id, offset, limit):
        rows = self.adapters["neo4j"].events(match_id, offset, limit)
        if rows is None:
            raise missing("el partido")
        return {"partido_id": match_id, "items": rows[:limit],
                "siguiente_offset": offset+limit if len(rows) > limit and offset+limit <= 10000 else None}

    def graph(self):
        return self.adapters["neo4j"].graph()

    def comments(self, match_id, query):
        partition = [match_id, query.bucket_10m.isoformat(), query.shard, query.limite]
        state = self.cursors.decode(query.cursor, partition)
        rows, next_state = self.adapters["cassandra"].comments(
            match_id, query.bucket_10m, query.shard, query.limite, state)
        for row in rows:
            if row["creado_en"].tzinfo is None:
                row["creado_en"] = row["creado_en"].replace(tzinfo=timezone.utc)
        return {"partido_id": match_id, "bucket_10m": query.bucket_10m, "shard": query.shard,
                "items": rows, "siguiente_cursor": self.cursors.encode(next_state, partition) if next_state else None}

    def session(self, session_id):
        result = self.adapters["redis"].session(session_id)
        if result is None:
            raise missing("una sesion vigente")
        return result

    def statistics(self, match_id, query):
        rows = self.adapters["influxdb"].statistics(match_id, query)
        return {"partido_id": match_id, "desde": query.desde, "hasta": query.hasta,
                "resolucion": query.resolucion, "items": rows[:1000], "truncado": len(rows) > 1000}

    def match(self, match_id, limit):
        result = self.adapters["iris"].match(match_id, limit)
        if result is None:
            raise missing("el objeto partido")
        return result

    def check(self, source):
        start = perf_counter()
        try:
            self.adapters[source].ping()
            status = "ok"
        except ApiError:
            status = "no_disponible"
        except Exception:
            status = "error"
        return {"estado": status, "duracion_ms": round((perf_counter()-start)*1000, 2)}
