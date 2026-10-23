import secrets

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    timeout_seconds: float = Field(default=5, ge=1, le=30)
    cursor_secret: SecretStr = Field(default_factory=lambda: SecretStr(secrets.token_hex(32)))
    mongo_uri: SecretStr = SecretStr("mongodb://localhost:27017")
    mongo_database: str = "fixture2030"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: SecretStr = SecretStr("")
    neo4j_database: str = "neo4j"
    cassandra_host: str = "localhost"
    cassandra_port: int = 9042
    cassandra_keyspace: str = Field(default="fixture2030_comentarios", pattern=r"^[a-z][a-z0-9_]*$")
    cassandra_datacenter: str = "datacenter1"
    cassandra_user: str = ""
    cassandra_password: SecretStr = SecretStr("")
    redis_url: SecretStr = SecretStr("redis://localhost:6379/0")
    influx_url: str = "http://localhost:8086"
    influx_database: str = "fixture2030"
    influx_mode: str = "v3"
    influx_org: str = "grupo9"
    influx_bucket: str = "estadisticas_live"
    influx_token: SecretStr = SecretStr("")
    iris_host: str = "localhost"
    iris_port: int = 1972
    iris_namespace: str = "USER"
    iris_user: str = "_SYSTEM"
    iris_password: SecretStr = SecretStr("")
