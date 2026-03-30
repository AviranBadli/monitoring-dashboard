from kubernetes import client, config as k8s_config
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    THANOS_URL: str = "http://localhost:9091"
    THANOS_TOKEN: str = ""
    TEST_ROW: bool = False

    model_config = {"env_file": ".env"}


settings = Settings()

# Initialize Kubernetes client and use kubeconfig token as fallback for THANOS_TOKEN
k8s_config.load_kube_config()
k8s_api = client.CustomObjectsApi()
batch_api = client.BatchV1Api()

if not settings.THANOS_TOKEN:
    k8s_cfg = k8s_config.kube_config.Configuration.get_default_copy()
    settings.THANOS_TOKEN = k8s_cfg.api_key.get("authorization", "").replace("Bearer ", "")
