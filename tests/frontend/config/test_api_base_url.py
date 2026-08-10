from src.config.api_url import normalize_api_base_url


def test_normalize_defaults_to_api_v1_without_trailing_slash() -> None:
    assert normalize_api_base_url(None) == "/api/v1"


def test_normalize_strips_trailing_slash() -> None:
    assert normalize_api_base_url("/api/v1/") == "/api/v1"
