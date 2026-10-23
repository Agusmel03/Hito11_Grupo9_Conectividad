class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, dependency: str | None = None):
        self.status = status
        self.code = code
        self.message = message
        self.dependency = dependency
        super().__init__(message)


def missing(resource: str):
    return ApiError(404, "recurso_inexistente", f"No existe {resource}.")


def unavailable(source: str):
    return ApiError(503, "dependencia_no_disponible", "No se pudo consultar la fuente de datos.", source)
