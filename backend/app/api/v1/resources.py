"""Reference/static data endpoints (clouds, teams, gpu-types, etc.)"""

from fastapi import APIRouter, Depends, HTTPException
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


@router.get("/clouds/{name}", response_model=CloudSchema)
def get_cloud(name: str, db: Session = Depends(get_db)):
    """Get a cloud provider by name"""
    cloud = db.query(Cloud).filter(Cloud.name == name).first()
    if not cloud:
        raise HTTPException(status_code=404, detail=f"Cloud '{name}' not found")
    return cloud


@router.post("/clouds", response_model=CloudSchema, status_code=201)
def create_cloud(cloud: CloudCreate, db: Session = Depends(get_db)):
    """Create a new cloud provider"""
    db_cloud = Cloud(name=cloud.name)
    db.add(db_cloud)
    db.commit()
    db.refresh(db_cloud)
    return db_cloud


@router.delete("/clouds/{name}", status_code=204)
def delete_cloud(name: str, db: Session = Depends(get_db)):
    """Delete a cloud provider"""
    cloud = db.query(Cloud).filter(Cloud.name == name).first()
    if not cloud:
        raise HTTPException(status_code=404, detail=f"Cloud '{name}' not found")
    db.delete(cloud)
    db.commit()


# Teams
@router.get("/teams", response_model=List[TeamSchema])
def list_teams(db: Session = Depends(get_db)):
    """List all teams"""
    return db.query(Team).all()


@router.get("/teams/{name}", response_model=TeamSchema)
def get_team(name: str, db: Session = Depends(get_db)):
    """Get a team by name"""
    team = db.query(Team).filter(Team.name == name).first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team '{name}' not found")
    return team


@router.post("/teams", response_model=TeamSchema, status_code=201)
def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    """Create a new team"""
    db_team = Team(name=team.name)
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


@router.delete("/teams/{name}", status_code=204)
def delete_team(name: str, db: Session = Depends(get_db)):
    """Delete a team"""
    team = db.query(Team).filter(Team.name == name).first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team '{name}' not found")
    db.delete(team)
    db.commit()


# GPU Types
@router.get("/gpu-types")
def list_gpu_types(db: Session = Depends(get_db)):
    """List all GPU types"""
    return db.query(GpuType).all()


@router.get("/gpu-types/{name}")
def get_gpu_type(name: str, db: Session = Depends(get_db)):
    """Get a GPU type by name"""
    gpu_type = db.query(GpuType).filter(GpuType.name == name).first()
    if not gpu_type:
        raise HTTPException(status_code=404, detail=f"GPU type '{name}' not found")
    return gpu_type


@router.post("/gpu-types", status_code=201)
def create_gpu_type(
    name: str,
    display_name: str,
    family: str,
    memory_gb: int = 0,
    variant: str = None,
    db: Session = Depends(get_db)
):
    """Create a new GPU type"""
    db_type = GpuType(
        name=name,
        display_name=display_name,
        family=family,
        memory_gb=memory_gb,
        variant=variant
    )
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type


@router.delete("/gpu-types/{name}", status_code=204)
def delete_gpu_type(name: str, db: Session = Depends(get_db)):
    """Delete a GPU type"""
    gpu_type = db.query(GpuType).filter(GpuType.name == name).first()
    if not gpu_type:
        raise HTTPException(status_code=404, detail=f"GPU type '{name}' not found")
    db.delete(gpu_type)
    db.commit()


# Workload Types
@router.get("/workload-types")
def list_workload_types(db: Session = Depends(get_db)):
    """List all workload types"""
    return db.query(WorkloadType).all()


@router.get("/workload-types/{name}")
def get_workload_type(name: str, db: Session = Depends(get_db)):
    """Get a workload type by name"""
    workload_type = db.query(WorkloadType).filter(WorkloadType.name == name).first()
    if not workload_type:
        raise HTTPException(status_code=404, detail=f"Workload type '{name}' not found")
    return workload_type


@router.post("/workload-types", status_code=201)
def create_workload_type(name: str, db: Session = Depends(get_db)):
    """Create a new workload type"""
    db_workload_type = WorkloadType(name=name)
    db.add(db_workload_type)
    db.commit()
    db.refresh(db_workload_type)
    return db_workload_type


@router.delete("/workload-types/{name}", status_code=204)
def delete_workload_type(name: str, db: Session = Depends(get_db)):
    """Delete a workload type"""
    workload_type = db.query(WorkloadType).filter(WorkloadType.name == name).first()
    if not workload_type:
        raise HTTPException(status_code=404, detail=f"Workload type '{name}' not found")
    db.delete(workload_type)
    db.commit()


# Allocation Types
@router.get("/allocation-types")
def list_allocation_types(db: Session = Depends(get_db)):
    """List all allocation types"""
    return db.query(AllocationType).all()


@router.get("/allocation-types/{name}")
def get_allocation_type(name: str, db: Session = Depends(get_db)):
    """Get an allocation type by name"""
    allocation_type = db.query(AllocationType).filter(AllocationType.name == name).first()
    if not allocation_type:
        raise HTTPException(status_code=404, detail=f"Allocation type '{name}' not found")
    return allocation_type


@router.post("/allocation-types", status_code=201)
def create_allocation_type(name: str, priority: int, db: Session = Depends(get_db)):
    """Create a new allocation type"""
    db_allocation_type = AllocationType(name=name, priority=priority)
    db.add(db_allocation_type)
    db.commit()
    db.refresh(db_allocation_type)
    return db_allocation_type


@router.delete("/allocation-types/{name}", status_code=204)
def delete_allocation_type(name: str, db: Session = Depends(get_db)):
    """Delete an allocation type"""
    allocation_type = db.query(AllocationType).filter(AllocationType.name == name).first()
    if not allocation_type:
        raise HTTPException(status_code=404, detail=f"Allocation type '{name}' not found")
    db.delete(allocation_type)
    db.commit()


# Instance Types
@router.get("/instance-types")
def list_instance_types(db: Session = Depends(get_db)):
    """List all instance types"""
    return db.query(InstanceType).all()


@router.get("/instance-types/{name}")
def get_instance_type(name: str, db: Session = Depends(get_db)):
    """Get an instance type by name"""
    instance_type = db.query(InstanceType).filter(InstanceType.name == name).first()
    if not instance_type:
        raise HTTPException(status_code=404, detail=f"Instance type '{name}' not found")
    return instance_type


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


@router.delete("/instance-types/{name}", status_code=204)
def delete_instance_type(name: str, db: Session = Depends(get_db)):
    """Delete an instance type"""
    instance_type = db.query(InstanceType).filter(InstanceType.name == name).first()
    if not instance_type:
        raise HTTPException(status_code=404, detail=f"Instance type '{name}' not found")
    db.delete(instance_type)
    db.commit()
