from pathlib import Path

from pydantic import ValidationError

from src.config.loader import ConfigLoader
#RendevouzManeger
from src.network.rendezvous.RendezvousManeger import RendezvousManeger
#CLI
from src.interface.cli import interpretar_comando, mostrar_ajuda
from src.interface.executar import executar_comando
#Game
from src.game.forca.gameHost import GameHost
from src.game.forca.gamePlayer import GamePlayer
from src.game.lobby.lobby import Lobby

def main() -> None:
    # Carregar as configurações
    project_root = Path(__file__).parent.parent
    file_path = project_root / "config.json"

    try:
        settings = ConfigLoader(file_path).load()
        print(settings.model_dump_json(indent=2))

    # Validar as configurações
    except ValidationError as error:
        # TODO: Passar os erros para o sistema de logs
        print("Configuração inválida")
        for detail in error.errors():
            field = ".".join(str(part) for part in detail["loc"])
            print(f"- {field or 'arquivo de configurações'}: {detail['msg']}")

    except (OSError, UnicodeError) as error:
        print("Não foi possível ler arquivo de configurações: ", error)

    # Criar Peer Local

    # Criar PeerTable (banco de dados)

    # Criar o ConnectionManager

    # Registra no Rendezvous
    config = settings.model_dump()
    rendezvous = RendezvousManeger(config)
    resposta = rendezvous.registrar()
    if resposta is not None and resposta.get("status") == "OK":
        print("Registrado no Rendezvous")
    else:
        print(f"Falha ao registrar no Rendezvous\nError: {resposta.get("message")}")

    # Descobre os Peers e faz conexão
    # Descobrir os Peers e fazer conexão
    resposta = rendezvous.descobrir_peers()
    if resposta is not None and resposta.get("status") == "OK":
        nomes = []
        for peer in rendezvous.peers:
            nomes.append(peer["name"])
        print("Peers encontrados:", nomes)
    else:
        print("Falha ao descobrir peers")

    #Criando elementos que são necessarios para a CLI
    config = settings.model_dump()
    #ID do peer
    peer_id = f"{config['name']}@{config['namespace']}"
    #Componentes do jogo
    game_host = GameHost(peer_id, config)
    game_player = GamePlayer(peer_id)
    lobby = Lobby(game_host, game_player)
    # Comandos da CLI
    print(f"\nBem vindo ao PyP2P-Forca 26.2, {peer_id}!!!")
    print("Digite /help para ver os comandos disponíveis.")
    while True:
        try:
            entrada = input("\npyp2p-forca> ").strip()
            # Ignora entradas vazias
            if not entrada:
                continue
            # Interpreta o comando digitado
            args = interpretar_comando(entrada)
            if args is None:
                continue
            # Comando /help
            if args["comando"] == "/help":
                mostrar_ajuda()
                continue
            # Comando /quit
            if args["comando"] == "/quit":
                print("Encerrando o programa...")
                break
            # Executa os demais comandos
            mensagem = executar_comando(args,game_host,config,lobby)
            #IMPELEMNTAR O ENVIO PELA REDE -> FUTURO

        except ValueError as erro:
            print(f"Comando inválido: {erro}")

        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando o programa...")
            break

    # Rotina de fechamento
    rendezvous.desregistrar()


if __name__ == "__main__":
    main()
