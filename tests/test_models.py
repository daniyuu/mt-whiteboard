import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from models import (
    Base,
    Whiteboard,
)


# Setup an in-memory SQLite database for testing
@pytest.fixture(scope="module")
def engine():
    return create_engine("sqlite:///:memory:")


@pytest.fixture(scope="module")
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(engine, tables):
    """Create a new session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# Sample data for testing
@pytest.fixture
def sample_whiteboard():
    return Whiteboard(name="Test Whiteboard")


# Test cases


def test_create_whiteboard(db_session, sample_whiteboard):
    db_session.add(sample_whiteboard)
    db_session.commit()

    whiteboard_from_db = (
        db_session.query(Whiteboard).filter_by(name="Test Whiteboard").one()
    )
    assert whiteboard_from_db.name == "Test Whiteboard"
    assert whiteboard_from_db.id is not None


def test_create_whiteboard_without_name(db_session):
    whiteboard = Whiteboard()
    db_session.add(whiteboard)
    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.asyncio
async def test_delete_whiteboard(db_session, sample_whiteboard):
    db_session.add(sample_whiteboard)
    db_session.commit()

    whiteboard_from_db = (
        db_session.query(Whiteboard).filter_by(name="Test Whiteboard").one()
    )
    await whiteboard_from_db.delete(db_session)
    db_session.commit()

    whiteboard_from_db = (
        db_session.query(Whiteboard)
        .filter(Whiteboard.deleted_at == None)
        .filter_by(name="Test Whiteboard")
        .one_or_none()
    )
    assert whiteboard_from_db is None
