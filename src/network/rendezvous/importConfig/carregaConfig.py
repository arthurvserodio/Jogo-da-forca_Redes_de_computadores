from pathlib import Path

from src.config.loader import ConfigLoader

from ..types import Config


def carregaConfig() -> Config:
    path = Path(__file__).resolve().parents[4] / "config.json"
    settings = ConfigLoader(path).load()
    return {
        "rdv_host": str(settings.rdv_host),
        "rdv_port": settings.rdv_port,
        "namespace": str(settings.namespace),
        "name": str(settings.name),
        "listen_port": settings.listen_port,
        "register_ttl": settings.register_ttl,
    }
