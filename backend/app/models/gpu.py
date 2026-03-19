"""GPU model"""

import re
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship, validates
from datetime import datetime, UTC

from app.core.database import Base


class GPU(Base):
    """Individual GPU discovered from DCGM metrics"""

    __tablename__ = "gpus"

    uuid = Column(String, primary_key=True, index=True)
    gpu_number = Column(Integer, nullable=False)  # GPU number within the node
    gpu_cluster = Column(String, nullable=False, index=True)  # From Prometheus labels
    node_name = Column(String, ForeignKey("gpu_nodes.name"), nullable=True)
    gpu_type_name = Column(String, ForeignKey("gpu_types.name"), nullable=False)

    # Metadata
    last_seen = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
    first_discovered = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    node = relationship("GPUNode", back_populates="gpus")
    gpu_type = relationship("GpuType", back_populates="gpus")

    # Table-level constraints
    # Note: CheckConstraint disabled for SQLite compatibility in tests
    # PostgreSQL constraint added via migration
    # __table_args__ = (
    #     CheckConstraint(
    #         "uuid ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'",
    #         name="gpu_uuid_format"
    #     ),
    # )

    @validates("uuid")
    def validate_uuid(self, key, value):
        """Validate and normalize UUID format"""
        if value is None:
            return value

        # Convert to lowercase for consistency
        value = value.lower().strip()

        # Validate UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
        )

        if not uuid_pattern.match(value):
            raise ValueError(
                f"Invalid UUID format: {value}. "
                "Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (hexadecimal)"
            )

        return value
