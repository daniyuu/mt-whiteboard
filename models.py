from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, TEXT, JSON
from datetime import datetime

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

    def delete(self):
        self.deleted_at = datetime.now()
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
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
        }

    def __repr__(self):
        return f"<Whiteboard {self.id}>"

    def delete(self):
        for node in self.nodes:
            node.delete()
        for edge in self.edges:
            edge.delete()
        super().delete()


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

    def delete(self):
        for edge in self.source_edges:
            edge.delete()
        for edge in self.target_edges:
            edge.delete()
        super().delete()

    def to_dict(self):
        return {
            "id": self.id,
            "whiteboard_id": self.whiteboard_id,
            "content": self.content,
            "status": self.status,
            "created_by": self.created_by,
            "extra_metadata": self.extra_metadata,
            "ui_attributes": self.ui_attributes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
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
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
        }
