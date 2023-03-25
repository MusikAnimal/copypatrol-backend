from __future__ import annotations

import pytest
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from copypatrol_backend import database
from copypatrol_backend.config import database_config


@pytest.fixture(scope="session")
def engine():
    return create_engine(URL.create(**database_config()), echo=True)


@pytest.fixture(scope="session")
def setup_database(engine):
    database._TableBase.metadata.drop_all(bind=engine)
    database._TableBase.metadata.create_all(bind=engine)
    yield
    database._TableBase.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine, setup_database):
    connection = engine.connect()
    transaction = connection.begin()
    session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=connection)
    )
    yield session
    session.close()
    transaction.rollback()
    connection.close()
