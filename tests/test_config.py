from apps.backend.app.core.config import settings


def test_settings_load_defaults():
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.PORT == 8000
    assert len(settings.cors_origins_list) > 0
    assert settings.STRICT_AIRGAP_ENFORCEMENT is True
    assert settings.ALLOW_EXTERNAL_EGRESS is False
