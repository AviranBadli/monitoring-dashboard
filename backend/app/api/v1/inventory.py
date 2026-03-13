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
