"""Instance Type model"""

import re
from sqlalchemy import Column, String, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship, validates

from app.core.database import Base


class InstanceType(Base):
    """Instance Type from cloud provider (e.g., p4d.24xlarge, Standard_NV36ads_A10_v5)"""

    __tablename__ = "instance_types"

    name = Column(String, primary_key=True, index=True)
    cloud_name = Column(String, ForeignKey("clouds.name"), nullable=False)
    gpu_type_name = Column(String, ForeignKey("gpu_types.name"), nullable=False)

    # Relationships
    cloud = relationship("Cloud", back_populates="instance_types")
    gpu_type = relationship("GpuType", back_populates="instance_types")
    nodes = relationship("GPUNode", back_populates="instance_type")
    cost_timeseries = relationship("CostTimeseries", back_populates="instance_type")

    # Table-level constraints
    # Note: CheckConstraint disabled for SQLite compatibility in tests
    # PostgreSQL constraint added via migration
    # __table_args__ = (
    #     CheckConstraint(
    #         "name ~ '^[a-z0-9._-]+$'",
    #         name="instance_type_name_format"
    #     ),
    # )

    @validates("name")
    def validate_name(self, key, value):
        """Validate and normalize instance type name

        Converts to lowercase and ensures only safe characters.
        Allows: alphanumeric, dots (.), hyphens (-), and underscores (_)
        Examples: p4d.24xlarge, standard_nc24s_v3, a2-highgpu-8g
        """
        if value is None:
            return value

        # Convert to lowercase for consistency
        value = value.lower()

        # Validate allowed characters
        if not re.match(r"^[a-z0-9._-]+$", value):
            # Remove any invalid characters
            value = re.sub(r"[^a-z0-9._-]", "", value)

        return value
