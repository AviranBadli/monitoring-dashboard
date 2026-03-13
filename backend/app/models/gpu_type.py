"""GPU Type model"""

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class GpuType(Base):
    """GPU Type (L4, T4, A100-40GB-SXM4, H100, etc.)"""

    __tablename__ = "gpu_types"

    name = Column(String, primary_key=True, index=True)

    # Relationships
    gpus = relationship("GPU", back_populates="gpu_type")
