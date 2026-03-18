"""GPU Type model"""

import re
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship, validates

from app.core.database import Base


class GpuType(Base):
    """GPU Type (L4, T4, A100-40GB-SXM4, H100, etc.)"""

    __tablename__ = "gpu_types"

    name = Column(String, primary_key=True, index=True)
    display_name = Column(String, nullable=False)
    family = Column(String, nullable=False)
    memory_gb = Column(Integer, nullable=False, default=0)
    variant = Column(String, nullable=True)

    # Relationships
    gpus = relationship("GPU", back_populates="gpu_type")

    # Table-level constraints
    # Note: CheckConstraint disabled for SQLite compatibility in tests
    # PostgreSQL constraint added via migration
    # __table_args__ = (
    #     CheckConstraint(
    #         "name ~ '^[a-z0-9]+(-[a-z0-9]+)*$'",
    #         name="gpu_type_name_kebab_case"
    #     ),
    # )

    @validates("name")
    def validate_name(self, key, value):
        """Validate and convert name to kebab-case"""
        if value is None:
            return value

        # Convert to kebab-case
        # Replace spaces and underscores with hyphens
        value = re.sub(r"[\s_]+", "-", value)
        # Remove any non-alphanumeric characters except hyphens
        value = re.sub(r"[^a-zA-Z0-9-]", "", value)
        # Convert to lowercase
        value = value.lower()
        # Remove multiple consecutive hyphens
        value = re.sub(r"-+", "-", value)
        # Remove leading/trailing hyphens
        value = value.strip("-")

        return value
