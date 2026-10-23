import json
#Método de discover
def DISCOVER(config):
    #Mensagem da operação DISCOVER 
    descubra = {
        "type": "DISCOVER",
        "namespace": config["namespace"],
    }
    #Transforma o dicionario em JSON
    return json.dumps(descubra) + "\n"

#Filtro da lista retornada no DISCOVER
#peers = lista devolvida pelo discover e meu_peer: quem eu sou como peer
def filtro_discover(peers,config):
    #Filtra a lista verificando o nome, ip e porta usada pelo peer
    peers_filtrados = list(filter(lambda peer: peer["name"]!=config["name"] or
                            peer["namespace"]!=config["namespace"], peers))
    return peers_filtrados