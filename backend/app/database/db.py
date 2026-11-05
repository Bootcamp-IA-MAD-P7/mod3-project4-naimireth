"""Motor, sesiones e inicializacion de la base de datos."""

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.database.models import Base


def build_engine(settings: Settings) -> Engine:
    url = settings.sqlalchemy_url
    connect_args = {"check_same_thread": False, "timeout": 30} if url.startswith("sqlite") else {}

    engine = create_engine(
        url,
        echo=settings.database_echo,
        connect_args=connect_args,
        future=True,
    )

    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)
