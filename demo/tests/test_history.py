import datetime
from unittest.mock import MagicMock, patch


from tests.conftest import mock_settings

from pages.history import (
    METRICS,
    build_dataframe,
    query_thanos_range,
)


class TestQueryThanosRange:
    def test_successful_query(self):
        mock_settings.THANOS_URL = "http://thanos:9091"
        mock_settings.THANOS_TOKEN = "test-token"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": "success",
            "data": {
                "result": [
                    {
                        "metric": {"localqueue": "lq-1", "exported_namespace": "ns-1"},
                        "values": [[1700000000, "3"]],
                    }
                ]
            },
        }

        start = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2024, 1, 1, 0, 15, tzinfo=datetime.timezone.utc)

        with patch("pages.history.httpx.get", return_value=mock_resp) as mock_get:
            result = query_thanos_range("test_metric", start, end, "10s")

        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["headers"]["Authorization"] == "Bearer test-token"
        assert call_kwargs.kwargs["params"]["query"] == "test_metric"
        assert call_kwargs.kwargs["params"]["step"] == "10s"
        assert len(result) == 1
        assert result[0]["values"] == [[1700000000, "3"]]

    def test_no_auth_header_without_token(self):
        mock_settings.THANOS_URL = "http://thanos:9091"
        mock_settings.THANOS_TOKEN = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "success", "data": {"result": []}}

        start = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2024, 1, 1, 0, 15, tzinfo=datetime.timezone.utc)

        with patch("pages.history.httpx.get", return_value=mock_resp) as mock_get:
            query_thanos_range("test_metric", start, end, "10s")

        assert "Authorization" not in mock_get.call_args.kwargs["headers"]

    def test_raises_on_failed_status(self):
        mock_settings.THANOS_URL = "http://thanos:9091"
        mock_settings.THANOS_TOKEN = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "error", "error": "bad query"}

        start = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2024, 1, 1, 0, 15, tzinfo=datetime.timezone.utc)

        with patch("pages.history.httpx.get", return_value=mock_resp):
            try:
                query_thanos_range("test_metric", start, end, "10s")
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "Thanos query failed" in str(e)


class TestBuildDataframe:
    def _make_thanos_result(self, metric_label, localqueue, namespace, values):
        return {
            "metric": {"localqueue": localqueue, "exported_namespace": namespace},
            "values": values,
        }

    def test_builds_dataframe_from_metrics(self):
        thanos_responses = {
            METRICS[0][0]: [
                self._make_thanos_result("Pending", "lq-1", "ns-1", [[1700000000, "2"]]),
            ],
            METRICS[1][0]: [
                self._make_thanos_result("Admitted", "lq-1", "ns-1", [[1700000000, "5"]]),
            ],
        }

        def fake_query(metric, start, end, step):
            return thanos_responses.get(metric, [])

        start = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2024, 1, 1, 0, 15, tzinfo=datetime.timezone.utc)

        with patch("pages.history.query_thanos_range", side_effect=fake_query):
            df = build_dataframe(start, end, "10s")

        assert len(df) == 2
        assert set(df["state"].unique()) == {"Pending", "Admitted"}
        assert all(df["queue"] == "ns-1/lq-1")
        pending_row = df[df["state"] == "Pending"].iloc[0]
        assert pending_row["count"] == 2.0
        admitted_row = df[df["state"] == "Admitted"].iloc[0]
        assert admitted_row["count"] == 5.0

    def test_empty_results_returns_empty_dataframe(self):
        with patch("pages.history.query_thanos_range", return_value=[]):
            start = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
            end = datetime.datetime(2024, 1, 1, 0, 15, tzinfo=datetime.timezone.utc)
            df = build_dataframe(start, end, "10s")

        assert df.empty
        assert list(df.columns) == ["time", "queue", "state", "count"]

    def test_multiple_queues(self):
        thanos_responses = {
            METRICS[0][0]: [
                self._make_thanos_result("Pending", "lq-1", "ns-1", [[1700000000, "1"]]),
                self._make_thanos_result("Pending", "lq-2", "ns-2", [[1700000000, "3"]]),
            ],
            METRICS[1][0]: [],
        }

        def fake_query(metric, start, end, step):
            return thanos_responses.get(metric, [])

        start = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2024, 1, 1, 0, 15, tzinfo=datetime.timezone.utc)

        with patch("pages.history.query_thanos_range", side_effect=fake_query):
            df = build_dataframe(start, end, "10s")

        assert len(df) == 2
        assert set(df["queue"].unique()) == {"ns-1/lq-1", "ns-2/lq-2"}

    def test_multiple_timestamps(self):
        thanos_responses = {
            METRICS[0][0]: [
                self._make_thanos_result(
                    "Pending", "lq-1", "ns-1", [[1700000000, "1"], [1700000010, "2"]]
                ),
            ],
            METRICS[1][0]: [],
        }

        def fake_query(metric, start, end, step):
            return thanos_responses.get(metric, [])

        start = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2024, 1, 1, 0, 15, tzinfo=datetime.timezone.utc)

        with patch("pages.history.query_thanos_range", side_effect=fake_query):
            df = build_dataframe(start, end, "10s")

        assert len(df) == 2
        assert df.iloc[0]["count"] == 1.0
        assert df.iloc[1]["count"] == 2.0

    def test_missing_metric_labels_default_to_unknown(self):
        thanos_responses = {
            METRICS[0][0]: [
                {
                    "metric": {},
                    "values": [[1700000000, "1"]],
                }
            ],
            METRICS[1][0]: [],
        }

        def fake_query(metric, start, end, step):
            return thanos_responses.get(metric, [])

        start = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2024, 1, 1, 0, 15, tzinfo=datetime.timezone.utc)

        with patch("pages.history.query_thanos_range", side_effect=fake_query):
            df = build_dataframe(start, end, "10s")

        assert df.iloc[0]["queue"] == "unknown/unknown"
