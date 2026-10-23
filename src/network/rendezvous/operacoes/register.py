import json

def REGISTER():
    #Nome para se registrar no Rendezvous
    nome = input("Digite seu nome de cadastro: ")
    #Mensagem de registro
    registro = {
        "type": "REGISTER",
        "namespace": "CIC",
        "name": nome,
        "port": 4000, #Porta do meu peer
        "ttl": 7200 #2h de ttl
    }

    #Converte o dicionario em json
    mensagemJSON = json.dumps(registro) + "\n"
    return mensagemJSON
