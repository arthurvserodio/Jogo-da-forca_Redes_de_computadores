from src.network.rendezvous.funcionalidades.funcoes import (
    registrar_peer,
    descobrir_peers,
    desregistrar_peer,
    refresh_peer,
    termina_refresh
)

# Registra o peer
respostaRegister = registrar_peer()

if respostaRegister and respostaRegister.get("status") == "OK":

    # Inicia o refresh
    parar, thread = refresh_peer(respostaRegister)

    try:
        # Descobre os peers
        peers = descobrir_peers()
        print("Peers encontrados:", peers)

        # Simula o jogo em execução
        input("Pressione Enter para sair...")

    finally:
        # Encerra o refresh
        termina_refresh(parar, thread)

        # Remove o registro
        desregistrar_peer()