from datetime import datetime, timezone
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

Code = Annotated[str, Field(pattern=r"^[A-Z]{3}$", examples=["AAA"])]
MatchID = Annotated[str, Field(pattern=r"^P[0-9]{3,9}$", examples=["P001"])]
SessionID = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,80}$", examples=["sess-demo-001"])]
Confederation = Literal["AFC", "CAF", "CONCACAF", "CONMEBOL", "OFC", "UEFA"]
T = TypeVar("T")


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Envelope(Model, Generic[T]):
    data: T


class Team(Model):
    id: str
    codigo_fifa: Code
    nombre: str
    confederacion: Confederation
    entrenador: str | None = None
    ranking_fifa: int | None = None


class Teams(Model):
    items: list[Team]
    siguiente_codigo: str | None


class GraphEvent(Model):
    id_evento: str
    tipo: str
    minuto: int
    descripcion: str | None = None
    jugador_id: str | None = None


class Events(Model):
    partido_id: MatchID
    items: list[GraphEvent]
    siguiente_offset: int | None


class GraphNode(Model):
    id: str
    tipo: str
    propiedades: dict[str, str | int | float | bool | None]


class GraphRelation(Model):
    id: str
    origen: str
    destino: str
    tipo: str
    propiedades: dict[str, str | int | float | bool | None]


class Graph(Model):
    nodos: list[GraphNode]
    relaciones: list[GraphRelation]
    total_nodos: int
    truncado: bool


class Comment(Model):
    comentario_id: UUID
    creado_en: datetime
    usuario_id: str
    contenido: str


class Comments(Model):
    partido_id: MatchID
    bucket_10m: AwareDatetime
    shard: int
    items: list[Comment]
    siguiente_cursor: str | None


class CommentQuery(Model):
    bucket_10m: AwareDatetime = Field(examples=["2030-06-10T18:00:00Z"])
    shard: int = Field(ge=0, le=7, default=0)
    limite: int = Field(default=25, ge=1, le=100)
    cursor: str | None = Field(default=None, max_length=8192)

    @model_validator(mode="after")
    def bucket_boundary(self):
        self.bucket_10m = self.bucket_10m.astimezone(timezone.utc)
        if self.bucket_10m.minute % 10 or self.bucket_10m.second or self.bucket_10m.microsecond:
            raise ValueError("bucket_10m debe comenzar en un multiplo de 10 minutos UTC")
        return self


class Session(Model):
    session_id: str
    estado: str
    ultima_actividad: str | None = None
    ttl_segundos: int = Field(ge=0)


class StatsQuery(Model):
    desde: AwareDatetime = Field(examples=["2030-06-08T19:00:00Z"])
    hasta: AwareDatetime = Field(examples=["2030-06-08T20:30:00Z"])
    equipo: Code | None = None
    resolucion: Literal["1m", "5m", "15m", "1h"] = "5m"

    @model_validator(mode="after")
    def valid_window(self):
        self.desde = self.desde.astimezone(timezone.utc)
        self.hasta = self.hasta.astimezone(timezone.utc)
        seconds = (self.hasta-self.desde).total_seconds()
        if not 0 < seconds <= 86400:
            raise ValueError("La ventana debe ser positiva y no superar 24 horas")
        return self


class StatsPoint(Model):
    tiempo: AwareDatetime
    equipo_codigo: str
    sede_id: str
    posesion_pct: float | None = None
    pases_completados_total: int | None = None
    tiros_intervalo: int | None = None
    recuperaciones_intervalo: int | None = None


class Statistics(Model):
    partido_id: MatchID
    desde: AwareDatetime
    hasta: AwareDatetime
    resolucion: str
    items: list[StatsPoint]
    truncado: bool


class ObjectEvent(Model):
    id: str
    tipo: str
    minuto: int
    descripcion: str


class MatchObject(Model):
    id: str
    partido_id: MatchID
    equipo_local: str
    equipo_visitante: str
    fecha: datetime
    sede: str
    estado: Literal["Programado", "EnCurso", "Finalizado"]
    eventos: list[ObjectEvent]
    eventos_truncados: bool


class ErrorDetail(Model):
    code: str
    message: str
    request_id: str
    dependency: str | None = None
    fields: list[str] = []


class ErrorResponse(Model):
    error: ErrorDetail


class DependencyStatus(Model):
    estado: Literal["ok", "no_disponible", "error"]
    duracion_ms: float


class Health(Model):
    estado: Literal["ok", "degradado"]
    dependencias: dict[str, DependencyStatus]
