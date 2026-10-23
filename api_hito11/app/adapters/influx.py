import json

from influxdb_client import InfluxDBClient
from influxdb_client.rest import ApiException
from urllib3.exceptions import HTTPError

from app.observability import guarded


class InfluxAdapter:
    def __init__(self, settings):
        self.settings = settings
        self.client = InfluxDBClient(url=settings.influx_url,
            token=settings.influx_token.get_secret_value(), org=settings.influx_org,
            timeout=int(settings.timeout_seconds*1000), retries=0)

    @guarded("influxdb", (ApiException, HTTPError, OSError))
    def statistics(self, match_id, query):
        quote = json.dumps
        start = query.desde.isoformat()
        stop = query.hasta.isoformat()
        script = f'''base = from(bucket: {quote(self.settings.influx_bucket)})
          |> range(start: time(v: {quote(start)}), stop: time(v: {quote(stop)}))
          |> filter(fn: (r) => r._measurement == "estadisticas_equipo" and r.partido_id == {quote(match_id)})
        '''
        if query.equipo:
            script += f' |> filter(fn: (r) => r.equipo_codigo == {quote(query.equipo)})\n'
        fields = [("posesion_pct", "mean"), ("pases_completados_total", "last"),
                  ("tiros_intervalo", "sum"), ("recuperaciones_intervalo", "sum")]
        for index, (field, function) in enumerate(fields):
            script += f'''f{index} = base |> filter(fn: (r) => r._field == "{field}")
                |> aggregateWindow(every: {query.resolucion}, fn: {function}, createEmpty: false)\n'''
        script += '''union(tables: [f0,f1,f2,f3])
          |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> group(columns: []) |> sort(columns: ["_time", "equipo_codigo", "sede_id"])
          |> limit(n: 1001)'''
        items = []
        for table in self.client.query_api().query(script):
            for record in table.records:
                items.append({"tiempo": record.get_time(), "equipo_codigo": record["equipo_codigo"],
                              "sede_id": record["sede_id"],
                              **{field: record.values.get(field) for field, _ in fields}})
        return items

    @guarded("influxdb", (ApiException, HTTPError, OSError))
    def ping(self):
        # A bucket read validates authorization as well as network availability.
        if self.client.buckets_api().find_bucket_by_name(self.settings.influx_bucket) is None:
            from app.errors import unavailable
            raise unavailable("influxdb")

    def close(self):
        self.client.close()
