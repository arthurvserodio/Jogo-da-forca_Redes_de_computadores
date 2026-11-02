import json

from ..types import Config


def UNREGISTER(config: Config) -> str:
    # Mensagem da operação UNREGISTER
    unregister = {
        "type": "UNREGISTER",
        "namespace": config["namespace"],
        "name": config["name"],
        "port": config["listen_port"],
    }

    # Coverte de dicionario para JSON
    return json.dumps(unregister) + "\n"
