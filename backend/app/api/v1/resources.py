"""Reference/static data endpoints (clouds, teams, gpu-types, etc.)"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db
from app.models import Cloud, Team, GpuType, WorkloadType, AllocationType, InstanceType
from app.schemas.cloud import Cloud as CloudSchema, CloudCreate
from app.schemas.team import Team as TeamSchema, TeamCreate

router = APIRouter()


# Clouds
@router.get("/clouds", response_model=List[CloudSchema])
def list_clouds(db: Session = Depends(get_db)):
    """List all cloud providers"""
    return db.query(Cloud).all()


@router.post("/clouds", response_model=CloudSchema, status_code=201)
def create_cloud(cloud: CloudCreate, db: Session = Depends(get_db)):
    """Create a new cloud provider"""
    db_cloud = Cloud(name=cloud.name)
    db.add(db_cloud)
    db.commit()
    db.refresh(db_cloud)
    return db_cloud


# Teams
@router.get("/teams", response_model=List[TeamSchema])
def list_teams(db: Session = Depends(get_db)):
    """List all teams"""
    return db.query(Team).all()


@router.post("/teams", response_model=TeamSchema, status_code=201)
def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    """Create a new team"""
    db_team = Team(name=team.name)
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


# GPU Types
@router.get("/gpu-types")
def list_gpu_types(db: Session = Depends(get_db)):
    """List all GPU types"""
    return db.query(GpuType).all()


@router.post("/gpu-types", status_code=201)
def create_gpu_type(name: str, db: Session = Depends(get_db)):
    """Create a new GPU type"""
    db_type = GpuType(name=name)
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type


# Workload Types
@router.get("/workload-types")
def list_workload_types(db: Session = Depends(get_db)):
    """List all workload types"""
    return db.query(WorkloadType).all()


# Allocation Types
@router.get("/allocation-types")
def list_allocation_types(db: Session = Depends(get_db)):
    """List all allocation types"""
    return db.query(AllocationType).all()


# Instance Types
@router.get("/instance-types")
def list_instance_types(db: Session = Depends(get_db)):
    """List all instance types"""
    return db.query(InstanceType).all()


@router.post("/instance-types", status_code=201)
def create_instance_type(
    name: str,
    cloud_name: str,
    gpu_type_name: str,
    gpu_count: float,
    instance_family: str,
    db: Session = Depends(get_db)
):
    """Create a new instance type"""
    db_instance_type = InstanceType(
        name=name,
        cloud_name=cloud_name,
        gpu_type_name=gpu_type_name,
        gpu_count=gpu_count,
        instance_family=instance_family
    )
    db.add(db_instance_type)
    db.commit()
    db.refresh(db_instance_type)
    return db_instance_type
