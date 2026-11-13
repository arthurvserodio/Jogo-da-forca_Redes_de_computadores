import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from src.config.loader import ConfigLoader
from src.config.settings import Settings


class ConfigTests(unittest.TestCase):
    def test_load_valid_config(self) -> None:
        path = Path(__file__).resolve().parents[1] / "config.json"
        settings = ConfigLoader(path).load()
        self.assertIsInstance(settings, Settings)
        self.assertEqual(settings.peer_id, f"{settings.name}@{settings.namespace}")
        self.assertGreaterEqual(settings.listen_port, 1)
        self.assertLessEqual(settings.listen_port, 65535)

    def test_invalid_config_raises_validation_error(self) -> None:
        with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as temp_file:
            temp_file.write('{"name": "", "rdv_port": 999999}')
            temp_path = Path(temp_file.name)

        try:
            with self.assertRaises(ValidationError):
                ConfigLoader(temp_path).load()
        finally:
            temp_path.unlink(missing_ok=True)
