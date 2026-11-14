from pathlib import Path

from src.config.settings import Settings


class ConfigLoader:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Settings:
        content = self.path.read_text(encoding="utf-8")
        return Settings.model_validate_json(content)
