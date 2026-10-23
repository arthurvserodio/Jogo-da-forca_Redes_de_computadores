import json
#Método de discover
def DISCOVER():
    #Mensagem da operação DISCOVER 
    descubra = {
        "type": "DISCOVER",
        "namespace": "CIC",
    }
    #Transforma o dicionario em JSON
    return json.dumps(descubra) + "\n"

#Filtro da lista retornada no DISCOVER
#peers = lista devolvida pelo discover e meu_peer: quem eu sou como peer
def filtro_discover(peers, meu_peer):
    #Filtra a lista verificando o nome, ip e porta usada pelo peer
    peers_filtrados = list(filter(lambda peer: peer["name"]!=meu_peer["name"] or
                            peer["ip"]!=meu_peer["ip"] or 
                            peer["port"]!=meu_peer["port"], peers))
    return peers_filtrados