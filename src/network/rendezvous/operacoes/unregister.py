import json

def UNREGISTER(config):
    #Mensagem da operação UNREGISTER
    unregister={
        "type": "UNREGISTER",
        "namespace": config["namespace"],
        "name": config["name"],
        "port": config["listen_port"]
    }

    #Coverte de dicionario para JSON
    return json.dumps(unregister) + "\n"