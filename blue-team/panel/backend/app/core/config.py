import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración del panel. Todo se lee de variables de entorno (ver .env.example)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    demo_mode: bool = True
    data_dir: Path = Path("./data")
    database_url: str = ""
    secret_key: str = ""

    admin_username: str = "admin"
    admin_password: str = ""

    access_token_minutes: int = 15
    refresh_token_hours: int = 8
    cookie_secure: bool = True
    allowed_origins: str = "https://localhost:8443"

    login_max_failures: int = 5
    login_window_minutes: int = 15
    login_lockout_max_minutes: int = 60
    login_ip_max_failures: int = 20

    enabled_connectors: str = "wazuh,suricata,kea,dns,pfsense,services,github"
    events_poll_seconds: float = 2.0
    state_poll_seconds: float = 30.0
    event_retention_days: int = 30
    demo_history_days: int = 7

    score_weights: str = "agents:20,vulnerabilities:20,hardening:20,alerts:20,coverage:20"
    severity_thresholds: str = Field(
        default="3,7,10,12",
        description="Nivel Wazuh mínimo para low,medium,high,critical",
    )

    wazuh_api_url: str = ""
    wazuh_api_user: str = ""
    wazuh_api_password: str = ""
    wazuh_indexer_url: str = ""
    wazuh_indexer_user: str = ""
    wazuh_indexer_password: str = ""
    wazuh_verify_tls: bool = False
    suricata_eve_path: str = "/var/log/suricata/eve.json"
    kea_leases_path: str = "/var/lib/kea/kea-leases4.csv"
    kea_config_path: str = "/etc/kea/kea-dhcp4.conf"
    github_token: str = ""
    github_project_url: str = ""

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def connectors(self) -> list[str]:
        return [c.strip() for c in self.enabled_connectors.split(",") if c.strip()]

    @property
    def wazuh_levels(self) -> tuple[int, int, int, int]:
        low, medium, high, critical = (int(x) for x in self.severity_thresholds.split(","))
        return low, medium, high, critical

    @property
    def db_url(self) -> str:
        return self.database_url or f"sqlite+aiosqlite:///{self.data_dir / 'panel.db'}"


def _ensure_secret_key(settings: Settings) -> None:
    """Si no hay SECRET_KEY se genera una y se guarda en el volumen de datos (nunca en el repo)."""
    if settings.secret_key:
        return
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    key_file = settings.data_dir / "secret_key"
    if key_file.exists():
        settings.secret_key = key_file.read_text().strip()
        return
    settings.secret_key = secrets.token_urlsafe(48)
    key_file.write_text(settings.secret_key)
    key_file.chmod(0o600)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    _ensure_secret_key(settings)
    return settings
