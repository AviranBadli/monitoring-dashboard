import sys
from unittest.mock import MagicMock

# Mock streamlit and config before any test module imports pages.demo
st_mock = MagicMock()
sys.modules["streamlit"] = st_mock

mock_k8s_api = MagicMock()
mock_core_api = MagicMock()
mock_settings = MagicMock()
mock_settings.TEST_ROW = False

config_mock = MagicMock()
config_mock.k8s_api = mock_k8s_api
config_mock.core_api = mock_core_api
config_mock.settings = mock_settings
sys.modules["config"] = config_mock
