import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


def _get_url() -> str:
    # Leemos la URL en cada llamada — permite sobreescribirla en tests con env var
    return os.getenv("DATABASE_URL", "sqlite:///leads.db")


@contextmanager
def get_session() -> Session:
    engine = create_engine(_get_url(), connect_args={"check_same_thread": False})
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


def get_engine():
    return create_engine(_get_url(), connect_args={"check_same_thread": False})
