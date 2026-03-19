"""GPU infrastructure inventory endpoints (clusters, nodes, gpus)"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db
from app.models import GPUCluster, GPUNode, GPU
from app.schemas.gpu import GPU as GPUSchema

router = APIRouter()


# Clusters
@router.get("/clusters")
def list_clusters(db: Session = Depends(get_db)):
    """List all GPU clusters"""
    return db.query(GPUCluster).all()


@router.get("/clusters/{cluster_name}")
def get_cluster(cluster_name: str, db: Session = Depends(get_db)):
    """Get a specific cluster with nodes"""
    cluster = db.query(GPUCluster).filter(GPUCluster.name == cluster_name).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster


@router.post("/clusters", status_code=201)
def create_cluster(
    name: str,
    cloud_name: str,
    owner_id: int = None,
    db: Session = Depends(get_db)
):
    """Create a new GPU cluster"""
    db_cluster = GPUCluster(
        name=name,
        cloud_name=cloud_name,
        owner_id=owner_id
    )
    db.add(db_cluster)
    db.commit()
    db.refresh(db_cluster)
    return db_cluster


@router.delete("/clusters/{cluster_name}", status_code=204)
def delete_cluster(cluster_name: str, db: Session = Depends(get_db)):
    """Delete a GPU cluster"""
    cluster = db.query(GPUCluster).filter(GPUCluster.name == cluster_name).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    db.delete(cluster)
    db.commit()


# Nodes
@router.get("/nodes")
def list_nodes(
    cluster_name: str | None = None,
    team_name: str | None = None,
    db: Session = Depends(get_db),
):
    """List GPU nodes, optionally filtered by cluster or team"""
    query = db.query(GPUNode)
    if cluster_name:
        query = query.filter(GPUNode.cluster_name == cluster_name)
    if team_name:
        query = query.filter(GPUNode.team_name == team_name)
    return query.all()


@router.get("/nodes/{node_name}")
def get_node(node_name: str, db: Session = Depends(get_db)):
    """Get a specific node with GPUs"""
    node = db.query(GPUNode).filter(GPUNode.name == node_name).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.post("/nodes", status_code=201)
def create_node(
    name: str,
    cluster_name: str,
    instance_type_name: str,
    team_name: str,
    region: str = None,
    db: Session = Depends(get_db)
):
    """Create a new GPU node"""
    db_node = GPUNode(
        name=name,
        cluster_name=cluster_name,
        instance_type_name=instance_type_name,
        team_name=team_name,
        region=region
    )
    db.add(db_node)
    db.commit()
    db.refresh(db_node)
    return db_node


@router.delete("/nodes/{node_name}", status_code=204)
def delete_node(node_name: str, db: Session = Depends(get_db)):
    """Delete a GPU node"""
    node = db.query(GPUNode).filter(GPUNode.name == node_name).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    db.delete(node)
    db.commit()


# GPUs
@router.get("/gpus", response_model=List[GPUSchema])
def list_gpus(
    cluster_name: str | None = None,
    node_name: str | None = None,
    gpu_type: str | None = None,
    db: Session = Depends(get_db),
):
    """List GPUs, optionally filtered"""
    query = db.query(GPU)
    if cluster_name:
        query = query.filter(GPU.gpu_cluster == cluster_name)
    if node_name:
        query = query.filter(GPU.node_name == node_name)
    if gpu_type:
        query = query.filter(GPU.gpu_type_name == gpu_type)
    return query.all()


@router.get("/gpus/{uuid}", response_model=GPUSchema)
def get_gpu(uuid: str, db: Session = Depends(get_db)):
    """Get a specific GPU by UUID"""
    gpu = db.query(GPU).filter(GPU.uuid == uuid).first()
    if not gpu:
        raise HTTPException(status_code=404, detail="GPU not found")
    return gpu


@router.post("/gpus", response_model=GPUSchema, status_code=201)
def create_gpu(
    uuid: str,
    gpu_number: int,
    gpu_cluster: str,
    gpu_type_name: str,
    node_name: str = None,
    db: Session = Depends(get_db)
):
    """Create a new GPU"""
    db_gpu = GPU(
        uuid=uuid,
        gpu_number=gpu_number,
        gpu_cluster=gpu_cluster,
        gpu_type_name=gpu_type_name,
        node_name=node_name
    )
    db.add(db_gpu)
    db.commit()
    db.refresh(db_gpu)
    return db_gpu


@router.delete("/gpus/{uuid}", status_code=204)
def delete_gpu(uuid: str, db: Session = Depends(get_db)):
    """Delete a GPU"""
    gpu = db.query(GPU).filter(GPU.uuid == uuid).first()
    if not gpu:
        raise HTTPException(status_code=404, detail="GPU not found")
    db.delete(gpu)
    db.commit()
