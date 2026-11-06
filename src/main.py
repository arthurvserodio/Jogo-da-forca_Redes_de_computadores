import argparse
from src.interface.cli import interpretar_comando,executar_comando
from src.game.forca.gameHost import GameHost
from src.network.rendezvous.importConfig.carregaConfig import carregaConfig

def main():
    # Carrega as configurações
    config = carregaConfig()

    # Identifica o peer local
    host_id = f"{config['name']}@{config['namespace']}"

    # Cria uma única instância do GameHost
    game_host = GameHost(host_id, config)

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
