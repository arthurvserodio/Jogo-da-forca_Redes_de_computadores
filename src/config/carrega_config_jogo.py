from pathlib import Path
from typing import cast

from src.config.loader import ConfigLoader
from src.config.types import ConfigJogo


def carregar_config_jogo() -> ConfigJogo:
    project_root = Path(__file__).resolve().parents[2]
    settings = ConfigLoader(project_root / "config.json").load()

    return cast(ConfigJogo, settings.model_dump())
