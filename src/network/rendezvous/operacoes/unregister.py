import json

def UNREGISTER(meu_peer):
    #Mensagem da operação UNREGISTER
    unregister={
        "type": "UNREGISTER",
        "namespace": "CIC",
        "name": meu_peer["name"],
        "port": meu_peer["port"]
    }

    #Coverte de dicionario para JSON
    return json.dumps(unregister) + "\n"