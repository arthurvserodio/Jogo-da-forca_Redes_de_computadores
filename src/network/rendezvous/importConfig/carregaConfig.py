import json

def carregaConfig():
    #Abre o config para leitura
    arquivo = open("config.json", "r", encoding="utf-8")
    #Transforma o JSON em dicionario
    config = json.load(arquivo)
    #Fecha o arquivo de leitura
    arquivo.close()
    return config