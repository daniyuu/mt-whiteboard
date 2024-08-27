from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, TEXT, JSON
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class BaseModels(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)

    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


class Whiteboard(BaseModels):
    __tablename__ = "whiteboard"
    name = Column(String(255), nullable=False)
    extra_metadata = Column(JSON, nullable=False, default={})
    ui_attributes = Column(JSON, nullable=False, default={})

    nodes = relationship(
        "Node", back_populates="whiteboard", cascade="all, delete-orphan"
    )
    edges = relationship(
        "Edge", back_populates="whiteboard", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "extra_metadata": self.extra_metadata,
            "ui_attributes": self.ui_attributes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

    def __repr__(self):
        return f"<Whiteboard {self.id}>"

    async def delete(self, session: AsyncSession):
        self.deleted_at = datetime.now()
        self.updated_at = datetime.now()

        whiteboard_nodes_query = select(Node).where(Node.whiteboard_id == self.id)
        whiteboard_edges_query = select(Edge).where(Edge.whiteboard_id == self.id)

        result_whiteboard_nodes = await session.execute(whiteboard_nodes_query)
        result_whiteboard_edges = await session.execute(whiteboard_edges_query)

        whiteboard_nodes = result_whiteboard_nodes.scalars().all()
        whiteboard_edges = result_whiteboard_edges.scalars().all()

        for node in whiteboard_nodes:
            node.deleted_at = datetime.now()
            node.updated_at = datetime.now()
            session.add(node)

        for edge in whiteboard_edges:
            edge.deleted_at = datetime.now()
            edge.updated_at = datetime.now()
            session.add(edge)

        session.add(self)
        await session.commit()


class Node(BaseModels):
    __tablename__ = "node"
    whiteboard_id = Column(Integer, ForeignKey("whiteboard.id"), nullable=False)
    content = Column(TEXT, nullable=False)
    status = Column(String(255), nullable=False)
    created_by = Column(String(255), nullable=False)

    extra_metadata = Column(JSON, nullable=False, default={})
    ui_attributes = Column(JSON, nullable=False, default={})

    whiteboard = relationship("Whiteboard", back_populates="nodes")
    source_edges = relationship(
        "Edge", foreign_keys="Edge.source_id", back_populates="source"
    )
    target_edges = relationship(
        "Edge", foreign_keys="Edge.target_id", back_populates="target"
    )

    async def delete(self, session: AsyncSession):
        self.deleted_at = datetime.now()
        self.updated_at = datetime.now()

        source_edges_query = select(Edge).where(Edge.source_id == self.id)
        target_edges_query = select(Edge).where(Edge.target_id == self.id)

        result_source_edges = await session.execute(source_edges_query)
        result_target_edges = await session.execute(target_edges_query)

        source_edges = result_source_edges.scalars().all()
        target_edges = result_target_edges.scalars().all()

        for edge in source_edges + target_edges:
            edge.deleted_at = datetime.now()
            edge.updated_at = datetime.now()
            session.add(edge)

        session.add(self)
        await session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "whiteboard_id": self.whiteboard_id,
            "content": self.content,
            "status": self.status,
            "created_by": self.created_by,
            "extra_metadata": self.extra_metadata,
            "ui_attributes": self.ui_attributes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class Edge(BaseModels):
    __tablename__ = "edge"
    whiteboard_id = Column(Integer, ForeignKey("whiteboard.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("node.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("node.id"), nullable=False)

    extra_metadata = Column(JSON, nullable=False, default={})
    ui_attributes = Column(JSON, nullable=False, default={})

    whiteboard = relationship("Whiteboard", back_populates="edges")
    source = relationship(
        "Node", foreign_keys=[source_id], back_populates="source_edges"
    )
    target = relationship(
        "Node", foreign_keys=[target_id], back_populates="target_edges"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "whiteboard_id": self.whiteboard_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "extra_metadata": self.extra_metadata,
            "ui_attributes": self.ui_attributes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

    def delete(self):
        self.deleted_at = datetime.now()
        self.updated_at = datetime.now()
