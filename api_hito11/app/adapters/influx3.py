import httpx


class Influx3Adapter:
    def __init__(self, settings):
        self.settings = settings
        self.url = settings.influx_url.rstrip("/")
        self.database = settings.influx_database
        self.token = settings.influx_token.get_secret_value()
        self.timeout = settings.timeout_seconds

    def query_sql(self, sql):
        response = httpx.get(
            f"{self.url}/api/v3/query_sql",
            params={
                "db": self.database,
                "q": sql,
                "format": "json",
            },
            headers={
                "Authorization": f"Bearer {self.token}",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def ping(self):
        rows = self.query_sql(
            "SELECT COUNT(*) AS total FROM estadisticas_equipo"
        )
        if not isinstance(rows, list):
            raise ValueError("Respuesta SQL inesperada")
        return True

    def close(self):
        pass