import datetime
import sys
from unittest.mock import MagicMock

# Mock streamlit, httpx and config before any test module imports pages
st_mock = MagicMock()
st_mock.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
st_mock.selectbox.return_value = 15
st_mock.date_input.return_value = datetime.date.today()
st_mock.multiselect.return_value = []
sys.modules["streamlit"] = st_mock

httpx_mock = MagicMock()
httpx_response = MagicMock()
httpx_response.json.return_value = {"status": "success", "data": {"result": []}}
httpx_mock.get.return_value = httpx_response
sys.modules["httpx"] = httpx_mock

mock_k8s_api = MagicMock()
mock_core_api = MagicMock()
mock_settings = MagicMock()
mock_settings.TEST_ROW = False
mock_settings.LOG_LEVEL = "INFO"

config_mock = MagicMock()
config_mock.k8s_api = mock_k8s_api
config_mock.core_api = mock_core_api
config_mock.settings = mock_settings
sys.modules["config"] = config_mock
