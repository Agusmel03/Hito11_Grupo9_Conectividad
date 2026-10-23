from threading import Lock

from cassandra import DriverException
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT, NoHostAvailable
from cassandra.policies import DCAwareRoundRobinPolicy, FallthroughRetryPolicy
from cassandra.query import dict_factory

from app.observability import guarded


class CassandraAdapter:
    def __init__(self, settings):
        self.settings = settings
        self.cluster = None
        self.session = None
        self.statement = None
        self.lock = Lock()

    def connect(self):
        with self.lock:
            if self.session is not None:
                return self.session
            settings = self.settings
            auth = PlainTextAuthProvider(settings.cassandra_user, settings.cassandra_password.get_secret_value()) if settings.cassandra_user else None
            profile = ExecutionProfile(
                load_balancing_policy=DCAwareRoundRobinPolicy(local_dc=settings.cassandra_datacenter),
                retry_policy=FallthroughRetryPolicy(), request_timeout=settings.timeout_seconds,
                row_factory=dict_factory)
            cluster = Cluster([settings.cassandra_host], port=settings.cassandra_port,
                              auth_provider=auth, connect_timeout=settings.timeout_seconds,
                              control_connection_timeout=settings.timeout_seconds,
                              execution_profiles={EXEC_PROFILE_DEFAULT: profile})
            try:
                session = cluster.connect(settings.cassandra_keyspace)
                statement = session.prepare("""SELECT comentario_id, creado_en, usuario_id, contenido
                    FROM comentarios_por_partido WHERE partido_id=? AND bucket_10m=? AND shard=?""")
            except Exception:
                cluster.shutdown()
                raise
            self.cluster, self.session, self.statement = cluster, session, statement
            return session

    @guarded("cassandra", (DriverException, NoHostAvailable, OSError))
    def comments(self, match_id, bucket, shard, limit, paging_state):
        session = self.connect()
        statement = self.statement.bind((match_id, bucket, shard))
        statement.fetch_size = limit
        result = session.execute(statement, paging_state=paging_state)
        # Iterating the ResultSet would fetch every page. Only expose current_rows.
        return list(result.current_rows), result.paging_state if result.has_more_pages else None

    @guarded("cassandra", (DriverException, NoHostAvailable, OSError))
    def ping(self):
        self.connect().execute("SELECT release_version FROM system.local")

    def close(self):
        if self.cluster:
            self.cluster.shutdown()
