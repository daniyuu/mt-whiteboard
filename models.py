from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BaseModels(Base):
    __abstract__ = True
    id = Column(String(255), primary_key=True)

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

        session.add(self)
        await session.commit()
