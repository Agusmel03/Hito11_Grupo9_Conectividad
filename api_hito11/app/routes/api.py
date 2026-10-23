import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.schemas.models import (Code, CommentQuery, Comments, Confederation, Envelope,
    ErrorResponse, Events, Health, MatchID, MatchObject, Session, SessionID,
    Statistics, StatsQuery, Team, Teams, Graph)

router = APIRouter(prefix="/api/v1", responses={
    422: {"model": ErrorResponse, "description": "Entrada invalida; no se consulta la fuente."},
    503: {"model": ErrorResponse, "description": "Dependencia inaccesible o timeout."},
    500: {"model": ErrorResponse, "description": "Error interno seguro."},
})
absent = {404: {"model": ErrorResponse, "description": "Recurso inexistente o sesion sin vigencia."}}


def service(request: Request):
    return request.app.state.service


@router.get("/grafo", tags=["Neo4j"], response_model=Envelope[Graph],
            summary="Explorar nodos y relaciones del Fixture",
            description="Instantanea de solo lectura: hasta 5000 nodos y 15000 relaciones del dominio. Propiedades publicas permitidas; truncado indica limites alcanzados. IDs internos validos solo para esta instantanea.")
def graph(svc=Depends(service)):
    return {"data": svc.graph()}


@router.get("/equipos", tags=["MongoDB"], response_model=Envelope[Teams], summary="Listar equipos")
def teams(svc=Depends(service), despues: Code | None = None,
          limite: int = Query(25, ge=1, le=100), confederacion: Confederation | None = None):
    return {"data": svc.teams(despues, limite, confederacion)}


@router.get("/equipos/{codigo}", tags=["MongoDB"], response_model=Envelope[Team], responses=absent,
            summary="Obtener un equipo por codigo FIFA")
def team(codigo: Code, svc=Depends(service)):
    return {"data": svc.team(codigo)}


@router.get("/partidos/{partido_id}/eventos", tags=["Neo4j"], response_model=Envelope[Events],
            responses=absent, summary="Consultar eventos y protagonistas de un partido")
def events(partido_id: MatchID, svc=Depends(service), limite: int = Query(25, ge=1, le=100),
           offset: int = Query(0, ge=0, le=10000)):
    return {"data": svc.events(partido_id, offset, limite)}


@router.get("/partidos/{partido_id}/comentarios", tags=["Cassandra"], response_model=Envelope[Comments],
            summary="Leer una particion de comentarios", description="Particion completa del Hito 6. Cursor firmado, valido por una hora y ligado a los parametros. Una particion vacia devuelve 200; no prueba existencia del partido en otros motores.")
def comments(partido_id: MatchID, query: Annotated[CommentQuery, Query()], svc=Depends(service)):
    return {"data": svc.comments(partido_id, query)}


@router.get("/sesiones/{session_id}", tags=["Redis"], response_model=Envelope[Session], responses=absent,
            summary="Consultar estado y TTL de una sesion", description="No devuelve usuario ni tokens. No renueva el TTL. Una sesion sin TTL, inactiva, ausente o expirada no es una sesion vigente.")
def session(session_id: SessionID, svc=Depends(service)):
    return {"data": svc.session(session_id)}


@router.get("/partidos/{partido_id}/estadisticas", tags=["InfluxDB"], response_model=Envelope[Statistics],
            summary="Agregar estadisticas en una ventana temporal", description="Intervalo [desde,hasta), maximo 24 horas. Posesion: mean; pases acumulados: last; tiros y recuperaciones: sum. Hasta 1000 filas; truncado=true requiere reducir la ventana o aumentar resolucion. tiempo es el final de la ventana Flux, que puede superar hasta en una ventana parcial.")
def statistics(partido_id: MatchID, query: Annotated[StatsQuery, Query()], svc=Depends(service)):
    return {"data": svc.statistics(partido_id, query)}


@router.get("/objetos/partidos/{partido_id}", tags=["IRIS"], response_model=Envelope[MatchObject],
            responses=absent, summary="Consultar un partido persistente y sus eventos hijos",
            description="Vista SQL de las clases Fixture2030.Partido y Evento del Hito 9. Fecha conserva el timestamp local original sin asignarle una zona no documentada.")
def match(partido_id: MatchID, svc=Depends(service), limite_eventos: int = Query(50, ge=1, le=100)):
    return {"data": svc.match(partido_id, limite_eventos)}


@router.get("/salud", tags=["Operacion"], response_model=Envelope[Health],
            responses={503: {"model": Envelope[Health], "description": "Una o mas dependencias no disponibles."}},
            summary="Comprobar conectividad real con las seis fuentes")
async def health(svc=Depends(service)):
    sources = list(svc.adapters)
    values = await asyncio.gather(*(run_in_threadpool(svc.check, source) for source in sources))
    ok = all(value["estado"] == "ok" for value in values)
    return JSONResponse(status_code=200 if ok else 503, content={"data": {
        "estado": "ok" if ok else "degradado", "dependencias": dict(zip(sources, values))}})
