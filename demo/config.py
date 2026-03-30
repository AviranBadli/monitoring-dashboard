from kubernetes import client, config as k8s_config
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TEST_ROW: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# Initialize Kubernetes client
k8s_config.load_kube_config()
k8s_api = client.CustomObjectsApi()
