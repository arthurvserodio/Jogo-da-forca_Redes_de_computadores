import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.network.rendezvous.funcionalidades.funcoes import desregistrar_peer
from src.network.rendezvous.importConfig.carregaConfig import carregaConfig
from src.network.rendezvous.operacoes.discover import filtro_discover
from src.network.rendezvous.operacoes.register import REGISTER


class RendezvousContracts(unittest.TestCase):
    def test_config_is_independent_of_working_directory(self) -> None:
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                self.assertIsInstance(carregaConfig()["rdv_port"], int)
            finally:
                os.chdir(previous)

    def test_register_is_one_json_line(self) -> None:
        config = carregaConfig()
        message = REGISTER(config)
        self.assertEqual(message.count("\n"), 1)
        self.assertEqual(json.loads(message)["port"], config["listen_port"])

    def test_discover_keeps_other_namespaces(self) -> None:
        config = carregaConfig()
        own = {"name": config["name"], "namespace": config["namespace"]}
        other = {"name": config["name"], "namespace": "OTHER"}
        self.assertEqual(filtro_discover([own, other], config), [other])

    def test_unregister_handles_connection_failure(self) -> None:
        with patch(
            "src.network.rendezvous.funcionalidades.funcoes.connectServer", return_value=None
        ):
            desregistrar_peer()
