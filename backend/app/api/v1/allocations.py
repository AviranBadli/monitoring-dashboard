"""GPU Node allocation endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from datetime import datetime

from app.api.deps import get_db
from app.models import Allocation, GPUNode
from app.schemas.allocation import (
    Allocation as AllocationSchema,
    AllocationCreate,
    AllocationUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[AllocationSchema])
def list_allocations(
    team_name: str | None = None,
    node_name: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    db: Session = Depends(get_db),
):
    """
    List allocations with optional filters.

    Query allocations by team, node, or time range.
    """
    query = db.query(Allocation)

    if team_name:
        query = query.filter(Allocation.team_name == team_name)
    if node_name:
        query = query.filter(Allocation.node_name == node_name)

    # Time range filtering: allocations that overlap with the query range
    if start_time and end_time:
        query = query.filter(
            and_(Allocation.start_time < end_time, Allocation.end_time > start_time)
        )
    elif start_time:
        query = query.filter(Allocation.end_time > start_time)
    elif end_time:
        query = query.filter(Allocation.start_time < end_time)

    return query.all()


@router.post("/", response_model=AllocationSchema, status_code=201)
def create_allocation(allocation: AllocationCreate, db: Session = Depends(get_db)):
    """
    Create a new node allocation.

    Validates that:
    - Node exists
    - No conflicting allocations exist
    - End time is after start time
    """
    # Validate node exists
    node = db.query(GPUNode).filter(GPUNode.name == allocation.node_name).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Validate time range
    if allocation.end_time <= allocation.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    # Check for conflicts
    conflicts = (
        db.query(Allocation)
        .filter(
            and_(
                Allocation.node_name == allocation.node_name,
                Allocation.start_time < allocation.end_time,
                Allocation.end_time > allocation.start_time,
            )
        )
        .all()
    )

    if conflicts:
        raise HTTPException(
            status_code=409,
            detail=f"Allocation conflicts with existing allocation(s): {[c.id for c in conflicts]}",
        )

    # Create allocation
    db_allocation = Allocation(**allocation.model_dump())
    db.add(db_allocation)
    db.commit()
    db.refresh(db_allocation)
    return db_allocation


@router.get("/{allocation_id}", response_model=AllocationSchema)
def get_allocation(allocation_id: int, db: Session = Depends(get_db)):
    """Get a specific allocation by ID"""
    allocation = db.query(Allocation).filter(Allocation.id == allocation_id).first()
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")
    return allocation


@router.patch("/{allocation_id}", response_model=AllocationSchema)
def update_allocation(allocation_id: int, updates: AllocationUpdate, db: Session = Depends(get_db)):
    """Update an allocation (e.g., extend end time)"""
    allocation = db.query(Allocation).filter(Allocation.id == allocation_id).first()
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")

    # Apply updates
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(allocation, field, value)

    db.commit()
    db.refresh(allocation)
    return allocation


@router.delete("/{allocation_id}", status_code=204)
def delete_allocation(allocation_id: int, db: Session = Depends(get_db)):
    """Delete an allocation"""
    allocation = db.query(Allocation).filter(Allocation.id == allocation_id).first()
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")

    db.delete(allocation)
    db.commit()
    return None
