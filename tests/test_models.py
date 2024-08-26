import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from models import (
    Base,
    Whiteboard,
    Node,
    Edge,
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


@pytest.fixture
def sample_node(sample_whiteboard):
    return Node(
        whiteboard=sample_whiteboard,
        content="Test content",
        status="active",
        created_by="tester",
        extra_metadata={"key": "value"},
        ui_attributes={"color": "blue"},
    )


# Test cases


def test_create_whiteboard(db_session, sample_whiteboard):
    db_session.add(sample_whiteboard)
    db_session.commit()

    whiteboard_from_db = (
        db_session.query(Whiteboard).filter_by(name="Test Whiteboard").one()
    )
    assert whiteboard_from_db.name == "Test Whiteboard"
    assert whiteboard_from_db.id is not None


def test_create_node(db_session, sample_whiteboard, sample_node):
    db_session.add(sample_whiteboard)
    db_session.add(sample_node)
    db_session.commit()

    node_from_db = db_session.query(Node).filter_by(content="Test content").one()
    assert node_from_db.content == "Test content"
    assert node_from_db.whiteboard_id == sample_whiteboard.id
    assert node_from_db.status == "active"
    assert node_from_db.created_by == "tester"
    assert node_from_db.extra_metadata == {"key": "value"}
    assert node_from_db.ui_attributes == {"color": "blue"}


def test_relationship(db_session, sample_whiteboard, sample_node):
    db_session.add(sample_whiteboard)
    db_session.add(sample_node)
    db_session.commit()

    whiteboard_from_db = (
        db_session.query(Whiteboard).filter_by(name="Test Whiteboard").one()
    )
    assert len(whiteboard_from_db.nodes) == 1
    assert whiteboard_from_db.nodes[0].content == "Test content"
    assert whiteboard_from_db.nodes[0].whiteboard_id == whiteboard_from_db.id
    assert whiteboard_from_db.nodes[0].status == "active"
    assert whiteboard_from_db.nodes[0].created_by == "tester"
    assert whiteboard_from_db.nodes[0].extra_metadata == {"key": "value"}
    assert whiteboard_from_db.nodes[0].ui_attributes == {"color": "blue"}


def test_create_whiteboard_without_name(db_session):
    whiteboard = Whiteboard()
    db_session.add(whiteboard)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_create_node_without_whiteboard(db_session):
    node = Node(
        content="Test content",
        status="active",
        created_by="tester",
        extra_metadata={"key": "value"},
        ui_attributes={"color": "blue"},
    )
    db_session.add(node)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_create_node_without_content(db_session, sample_whiteboard):
    node = Node(
        whiteboard=sample_whiteboard,
        status="active",
        created_by="tester",
        extra_metadata={"key": "value"},
        ui_attributes={"color": "blue"},
    )
    db_session.add(node)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_create_edge(db_session, sample_whiteboard, sample_node):
    edge = Edge(
        whiteboard=sample_whiteboard,
        source=sample_node,
        target=sample_node,
        extra_metadata={"key": "value"},
    )
    db_session.add(sample_whiteboard)
    db_session.add(sample_node)
    db_session.add(edge)
    db_session.commit()

    edge_from_db = (
        db_session.query(Edge).filter_by(whiteboard_id=sample_whiteboard.id).one()
    )
    assert edge_from_db.whiteboard_id == sample_whiteboard.id
    assert edge_from_db.source_id == sample_node.id
    assert edge_from_db.target_id == sample_node.id
    assert edge_from_db.extra_metadata == {"key": "value"}


def test_create_edge_without_whiteboard(db_session, sample_node):
    edge = Edge(
        source=sample_node,
        target=sample_node,
        extra_metadata={"key": "value"},
    )
    db_session.add(edge)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_create_edge_without_source(db_session, sample_whiteboard):
    edge = Edge(
        whiteboard=sample_whiteboard,
        target_id=1,
        extra_metadata={"key": "value"},
    )
    db_session.add(edge)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_create_edge_without_target(db_session, sample_whiteboard):
    edge = Edge(
        whiteboard=sample_whiteboard,
        source_id=1,
        extra_metadata={"key": "value"},
    )
    db_session.add(edge)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_create_multiple_edges(db_session, sample_whiteboard, sample_node):
    edge1 = Edge(
        whiteboard=sample_whiteboard,
        source=sample_node,
        target=sample_node,
        extra_metadata={"key": "value"},
    )
    edge2 = Edge(
        whiteboard=sample_whiteboard,
        source=sample_node,
        target=sample_node,
        extra_metadata={"key": "value"},
    )
    db_session.add(sample_whiteboard)
    db_session.add(sample_node)
    db_session.add(edge1)
    db_session.add(edge2)
    db_session.commit()

    edges_from_db = (
        db_session.query(Edge).filter_by(whiteboard_id=sample_whiteboard.id).all()
    )
    assert len(edges_from_db) == 2
    assert edges_from_db[0].source_id == sample_node.id
    assert edges_from_db[1].source_id == sample_node.id
    assert edges_from_db[0].target_id == sample_node.id
    assert edges_from_db[1].target_id == sample_node.id
    assert edges_from_db[0].extra_metadata == {"key": "value"}
    assert edges_from_db[1].extra_metadata == {"key": "value"}


def test_delete_whiteboard(db_session, sample_whiteboard):
    db_session.add(sample_whiteboard)
    db_session.commit()

    whiteboard_from_db = (
        db_session.query(Whiteboard).filter_by(name="Test Whiteboard").one()
    )
    whiteboard_from_db.delete()
    db_session.commit()

    whiteboard_from_db = (
        db_session.query(Whiteboard)
        .filter(Whiteboard.deleted_at == None)
        .filter_by(name="Test Whiteboard")
        .one_or_none()
    )
    assert whiteboard_from_db is None


def test_delete_node(db_session, sample_whiteboard, sample_node):
    db_session.add(sample_whiteboard)
    db_session.add(sample_node)
    db_session.commit()

    node_from_db = db_session.query(Node).filter_by(content="Test content").one()
    node_from_db.delete()
    db_session.commit()

    node_from_db = (
        db_session.query(Node)
        .filter(Node.deleted_at == None)
        .filter_by(content="Test content")
        .one_or_none()
    )
    assert node_from_db is None


def test_delete_edge(db_session, sample_whiteboard, sample_node):
    edge = Edge(
        whiteboard=sample_whiteboard,
        source=sample_node,
        target=sample_node,
        extra_metadata={"key": "value"},
    )
    db_session.add(sample_whiteboard)
    db_session.add(sample_node)
    db_session.add(edge)
    db_session.commit()

    edge_from_db = (
        db_session.query(Edge).filter_by(whiteboard_id=sample_whiteboard.id).one()
    )
    edge_from_db.delete()
    db_session.commit()

    edge_from_db = (
        db_session.query(Edge)
        .filter(Edge.deleted_at == None)
        .filter_by(whiteboard_id=sample_whiteboard.id)
        .one_or_none()
    )
    assert edge_from_db is None


def test_delete_whiteboard_cascade(db_session, sample_whiteboard, sample_node):
    db_session.add(sample_whiteboard)
    db_session.add(sample_node)
    db_session.commit()

    whiteboard_from_db = (
        db_session.query(Whiteboard).filter_by(name="Test Whiteboard").one()
    )
    whiteboard_from_db.delete()
    db_session.commit()

    whiteboard_from_db = (
        db_session.query(Whiteboard)
        .filter(Whiteboard.deleted_at == None)
        .filter_by(name="Test Whiteboard")
        .one_or_none()
    )
    assert whiteboard_from_db is None

    node_from_db = (
        db_session.query(Node)
        .filter(Node.deleted_at == None)
        .filter_by(content="Test content")
        .one_or_none()
    )
    assert node_from_db is None


def test_delete_node_cascade(db_session, sample_whiteboard, sample_node):
    edge = Edge(
        whiteboard=sample_whiteboard,
        source=sample_node,
        target=sample_node,
        extra_metadata={"key": "value"},
    )
    db_session.add(sample_whiteboard)
    db_session.add(sample_node)
    db_session.add(edge)
    db_session.commit()

    node_from_db = db_session.query(Node).filter_by(content="Test content").one()
    node_from_db.delete()
    db_session.commit()

    node_from_db = (
        db_session.query(Node)
        .filter(Node.deleted_at == None)
        .filter_by(content="Test content")
        .one_or_none()
    )
    assert node_from_db is None

    edge_from_db = (
        db_session.query(Edge)
        .filter(Edge.deleted_at == None)
        .filter_by(whiteboard_id=sample_whiteboard.id)
        .one_or_none()
    )
    assert edge_from_db is None
