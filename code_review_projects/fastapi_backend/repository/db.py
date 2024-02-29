from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session as SQLSession

from fastapi_backend.config import ApplicationSettings
from fastapi_backend.models import Base

engine = None


class WrongQueryError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def get_engine():
    global engine
    settings = ApplicationSettings()
    if engine is None:
        engine = create_engine(
            settings.database_path,
            pool_size=settings.connection_pool_size,
            max_overflow=settings.connection_pool_max_overflow,
            pool_recycle=3600,
            connect_args={"options": "-c timezone=utc"},
            isolation_level="READ COMMITTED",
        )
    return engine


@contextmanager
def Session() -> SQLSession:
    _engine = get_engine()
    session = SQLSession(bind=_engine)
    try:
        yield session
    except:
        session.rollback()
        raise
    finally:
        session.close()


def truncate_db():
    engine = get_engine()
    meta = Base.metadata
    conn = engine.connect()
    txn = conn.begin()
    for t in meta.sorted_tables:
        if hasattr(t, "info") and t.info.get("is_view", False):
            continue
        if t.name == "freeze_time_param_type":
            continue
        conn.execute(f'ALTER TABLE "{t.name}" DISABLE TRIGGER ALL;')
        conn.execute(t.delete())
        conn.execute(f'ALTER TABLE "{t.name}" ENABLE TRIGGER ALL;')

    for seq in [
        "campaign_input_id_seq",
        "campaign_parameters_id_seq",
        "customer_id_seq",
        "harvey_campaign_id_seq",
        "report_id_seq",
    ]:
        conn.execute(f"ALTER SEQUENCE {seq} RESTART WITH 1;")
    txn.commit()
