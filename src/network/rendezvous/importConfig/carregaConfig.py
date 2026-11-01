import json
from pathlib import Path
from typing import cast

from ..types import Config


def carregaConfig() -> Config:
    path = Path(__file__).resolve().parents[4] / "config.json"
    with path.open(encoding="utf-8") as arquivo:
        return cast(Config, json.load(arquivo))
