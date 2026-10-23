from contextlib import closing
import iris.dbapi

from app.observability import guarded


class IrisAdapter:
    def __init__(self, settings):
        self.settings = settings

    def connect(self):
        s = self.settings
        return iris.dbapi.connect(hostname=s.iris_host, port=s.iris_port,
            namespace=s.iris_namespace, username=s.iris_user,
            password=s.iris_password.get_secret_value(), timeout=int(s.timeout_seconds),
            sharedmemory=False)

    @guarded("iris", (iris.dbapi.Error, OSError))
    def match(self, match_id, limit):
        with closing(self.connect()) as connection, closing(connection.cursor()) as cursor:
            cursor.execute("""SELECT ID, PartidoID, EquipoLocal, EquipoVisitante, Fecha, Sede, Estado
                              FROM Fixture2030.Partido WHERE PartidoID = ?""", [match_id])
            row = cursor.fetchone()
            if row is None:
                return None
            result = dict(zip(["id", "partido_id", "equipo_local", "equipo_visitante", "fecha", "sede", "estado"], row))
            result["id"] = str(result["id"])
            cursor.execute("""SELECT TOP ? ID, Tipo, Minuto, Descripcion FROM Fixture2030.Evento
                              WHERE Partido = ? ORDER BY Minuto, ID""", [limit+1, row[0]])
            events = [{"id": str(r[0]), "tipo": r[1], "minuto": r[2], "descripcion": r[3]}
                      for r in cursor.fetchall()]
            return {**result, "eventos": events[:limit], "eventos_truncados": len(events) > limit}

    @guarded("iris", (iris.dbapi.Error, OSError))
    def ping(self):
        with closing(self.connect()) as connection, closing(connection.cursor()) as cursor:
            cursor.execute("SELECT TOP 1 PartidoID FROM Fixture2030.Partido")
            cursor.fetchone()

    def close(self):
        pass
