import json

def REGISTER(config):
    #Mensagem de registro
    registro = {
        "type": "REGISTER",
        "namespace": config["namespace"],
        "name": config["name"],
        "port": config["listen_port"], #Porta do meu peer
        "ttl": config["register_ttl"] #2h de ttl
    }

    #Converte o dicionario em json
    mensagemJSON = json.dumps(registro) + "\n"
    return mensagemJSON
