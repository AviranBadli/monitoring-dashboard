import os

from kubernetes import client, config as k8s_config
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TEST_ROW: bool = False
    SHOW_MIG: bool = False
    SHOW_GPU_UTIL: bool = False
    THANOS_URL: str = "https://thanos-querier.openshift-monitoring.svc.cluster.local:9091"
    THANOS_TOKEN: str = ""
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# Use the pod's service account token for Thanos auth when no token is configured
if not settings.THANOS_TOKEN:
    sa_token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    if os.path.exists(sa_token_path):
        with open(sa_token_path) as f:
            settings.THANOS_TOKEN = f.read().strip()

# Initialize Kubernetes client — use in-cluster config when available, fall back to kubeconfig
try:
    k8s_config.load_incluster_config()
except k8s_config.ConfigException:
    k8s_config.load_kube_config()
k8s_api = client.CustomObjectsApi()
core_api = client.CoreV1Api()
