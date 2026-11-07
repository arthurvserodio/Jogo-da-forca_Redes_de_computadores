import argparse
import logging
from src.interface.cli import interpretar_comando
from src.interface.executar import executar_comando
from src.game.forca.gameHost import GameHost
from src.network.rendezvous.importConfig.carregaConfig import carregaConfig
from src.interface.executar import mostra_status_jogo
def main():
    # Carrega as configurações
    config = carregaConfig()

    # Identifica o peer local
    host_id = f"{config['name']}@{config['namespace']}"

    # Cria uma única instância do GameHost
    game_host = GameHost(host_id, config)
    logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
    game_host.criar_jogo("banana", 6)
    game_host.adicionar_jogador("bob@CIC", None)
    game_host.iniciar_jogo()

    status = game_host.obter_status()
    mostra_status_jogo(status, config)

    # Loop interativo
    while True:
        try:
            entrada = input("PyP2P-Forca > ")

            resultado = interpretar_comando(entrada)

            if resultado is None:
                continue

            if resultado["comando"] == "/quit":
                print("Encerrando programa...")
                break

            executar_comando(resultado, game_host, config)

        except (ValueError, argparse.ArgumentError) as erro:
            print(f"Erro: {erro}")

        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando programa...")
            break


if __name__ == "__main__":
    main()
