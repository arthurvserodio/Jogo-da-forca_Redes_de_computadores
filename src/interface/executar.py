import logging
import random
from typing import Any

from src.config.types import ConfigJogo
from src.game.lobby.lobby import Lobby
from src.interface.cli import mostrar_Game, mostrar_Host, mostrar_Player
from src.interface.desenha_forca import desenha_forca
from src.network.rendezvous.RendezvousManeger import RendezvousManeger


def executar_comando(
    args: dict[str, Any],
    game_host: Any,
    config: ConfigJogo,
    lobby: Lobby | None = None,
    rendezvous: RendezvousManeger | None = None,
) -> dict[str, Any] | None:
    comando = args["comando"]
    # COMANDO DO HOST
    # Executar o /create
    if comando == "/create":
        # Se for --random
        if args["random"]:
            # Pega uma palavra do arquivo word
            with open("words.txt", encoding="utf-8") as arquivo:
                conteudo = arquivo.read()
                list_palavra = conteudo.split()
                palavra = random.choice(
                    list_palavra
                )  # random choice para pegar uma palavra aleatoria
        else:
            palavra = args["palavra"]

        # Obtém a quantidade máxima de jogadores
        max_players = args["max_players"]
        sucesso = game_host.criar_jogo(palavra, config["lives"], max_players)
        if sucesso["aceito"]:
            mostrar_Host(sucesso["mensagem"])
            mostrar_Host(f"ID: {game_host.game_id}")
            mostrar_Host(f"Palavra: {palavra} | Vidas: {config['lives']}")
            mostrar_Host(
                f"Jogadores: 0/{game_host.max_players} | Estado: {game_host.game_state.name}"
            )
        else:
            mostrar_Host("Não foi possível criar a partida.")
            mostrar_Host(sucesso["mensagem"])
    # Executar o /start
    elif comando == "/start":
        sucesso = game_host.iniciar_jogo()
        if sucesso["aceito"]:
            mostrar_Host(sucesso["mensagem"])
            mostrar_Host(f"Jogadores participanates: {game_host.players}")
            mostrar_Host(f"Primeiro turno: {game_host.turno_atual}")
        else:
            mostrar_Host("Não foi possível iniciar a partida.")
            mostrar_Host(sucesso["mensagem"])
    # Executar o /cancel
    elif comando == "/cancel":
        sucesso = game_host.cancelar_jogo()
        if sucesso:
            mostrar_Host("Partida cancelada pelo Host!")
        else:
            if game_host.game_state.name != "OPEN":
                mostrar_Host(
                    "Não foi possível cancelar a partida, pois ela não abriu ou foi finalizada."
                )

    # COMANDO DO LOOBY
    # Executar o /games
    elif comando == "/games":
        # Se não existir nada, não pode fazer nada
        if lobby is None:
            return None
        # Solicita ao lobby a criação da mensagem GAME_LIST
        mensagem = lobby.gerar_mensagem_GAMELIST()
        mostrar_Game("Consultando partidas disponíveis...")
        # Devolve a mensagem para a camada de comunicação
        return mensagem

    # Executar o /join
    elif comando == "/join":
        # Se não existir nada, não pode fazer nada
        if lobby is None:
            return None
        host_id = args["host_peer_id"]
        # Busca partida hospedada por esse host
        partida = lobby.partidas_encontradas.get(host_id)
        # Se a partida não foi encontrada para esse host ou ela não está em OPEN, não tem como fazer o join
        if partida is None or partida["status"] != "OPEN":
            mostrar_Player(f"Nenhuma partida aberta encontrada para {host_id}")
            return None

        # Gera a solicitação JOIN
        mensagem = lobby.mensagemJOIN(partida["game_id"])
        mostrar_Game(f"Solicitando entrada na partida de {host_id}")
        return mensagem

    # Executar o /leave
    elif comando == "/leave":
        # Se não existir nada, não pode fazer nada
        if lobby is None:
            return None
        # Gera a mensagem LEAVE
        mensagem_leave = lobby.mensagemLEAVE()
        if mensagem_leave is None:
            mostrar_Game("Você não está participando de nenhuma partida.")
            return None
        mostrar_Game("Solicitando a saída da partida...")
        return mensagem_leave

    # COMANDO DO JOGADOR
    # Executar o /guess ou /word
    elif comando == "/guess" or comando == "/word":
        if lobby is None:
            mostrar_Game("Lobby não disponível.")
            return None
        # Pega o palpite
        if comando == "/guess":
            palpite = args["letra"]
        else:
            palpite = args["palavra"]
        mensagem_guess: dict[str, Any] | None = lobby.game_player.gerar_guess(palpite)
        if mensagem_guess is None:
            mostrar_Game(
                "Não foi possível enviar o palpite. Verifique se você está jogando e se é sua vez."
            )

        return mensagem_guess

    # Executar o /status
    elif comando == "/status":
        # Verifica se está hospedando uma partida
        status = game_host.obter_status()
        # Caso não esteja hospedando, verifica a partida em que o peer participa
        if status is None and lobby is not None:
            jogador = lobby.game_player
            if jogador.estado.name == "PLAYING":
                status = {
                    "game_id": jogador.game_id,
                    "host_id": jogador.host_id,
                    "estado": "RUNNING",
                    "palavra_mask": " ".join(jogador.mask_word or ""),
                    "vidas": jogador.vidas,
                    "letras_erradas": jogador.letras_erradas,
                    "jogadores": jogador.players,
                    "turno_atual": jogador.turno,
                }
            elif jogador.estado.name == "JOINED":
                mostrar_Game(f"Partida: {jogador.game_id}")
                mostrar_Game(f"Host: {jogador.host_id}")
                mostrar_Game("Estado: OPEN")
                return None
        if status is None:
            mostrar_Game("Nenhuma partida encontrada.")
            return None
        if status["estado"] == "OPEN":
            mostrar_Game(f"Partida: {status['game_id']}")
            mostrar_Game("Estado: OPEN")

            if "jogadores" in status:
                mostrar_Game(f"Jogadores: {len(status['jogadores'])}/{status['max_players']}")
        elif status["estado"] == "RUNNING":
            mostra_status_jogo(status, config)
        else:
            mostrar_Game(f"Estado: {status['estado']}")
        return None

    # COMANDOS DE REDE
    # Executando /peers
    elif comando == "/peers":
        if rendezvous is None:
            print("Rendezvous não disponível.")
            return None
        filtro = args["filtro"]
        # Consulta os peers no rendezvous
        resposta = rendezvous.descobrir_peers()
        # Se retornou None ou ERROR é pq deu errado
        if resposta is None or resposta["status"] != "OK":
            print("Não foi possível consultar os peers")
            return None
        peers = rendezvous.peers
        # Filtra por namespace
        if filtro is not None and filtro != "*":
            namespace = filtro[1:]
            # Só coloca em peers filtrados aqueles que tem o namespace desejado
            peers_filter = [peer for peer in peers if peer["namespace"] == namespace]
        else:
            peers_filter = peers.copy()

        if len(peers_filter) == 0:
            print("Nenhum peer encontrado.")
            return None

        # Exibe os peers
        print("Peers disponíveis:")
        for peer in peers_filter:
            print(f"- {peer['name']}@{peer['namespace']}")

    # Executando /conn
    elif comando == "/conn":
        print("Consultando conexões ativas...")

    # Executando /rtt
    elif comando == "/rtt":
        print("Consultando RTT dos peers...")

    # Executando /reconnect
    elif comando == "/reconnect":
        print("Solicitando reconexão...")

    # CONFIGURAÇÕES
    # Executando /log
    elif comando == "/log":
        nivel = args["nivel"]
        logging.getLogger().setLevel(getattr(logging, nivel))
        print(f"Nível de log alterado para {nivel}")
        logging.debug("Teste DEBUG")
        logging.info("Teste INFO")
        logging.warning("Teste WARNING")
        logging.error("Teste ERROR")

    return None


# Status do jogo RUNNING - Mostra quando dá /status ou muda STATE
def mostra_status_jogo(status: dict[str, Any], config: ConfigJogo) -> None:
    vidas = status["vidas"]
    # Descobre a quantidade de erros cometidos
    erros = max(0, config["lives"] - vidas)
    # Desenho da forca
    print(desenha_forca(erros))
    mostrar_Game(f"{status['game_id']}  (host: {status['host_id']})  status: {status['estado']}")
    mostrar_Game(
        f"Palavra: {status['palavra_mask']}     Vidas: {status['vidas']} / {config['lives']}     Erradas: {', '.join(status['letras_erradas'])}"
    )
    mostrar_Game(f"Jogadores: {', '.join(status['jogadores'])}   Vez de: {status['turno_atual']}")


# Mostra as mensagens finais do jogo
def mostra_gameOver(mensagem: dict[str, Any]) -> None:
    resultado = mensagem["result"]
    palavra = mensagem["word"]
    vencedor = mensagem.get("winner")
    pontuacoes = mensagem.get("scores", {})

    mostrar_Game("========== PARTIDA FINALIZADA ==========")

    if resultado == "WON":
        mostrar_Game("Resultado: VITÓRIA!")
        mostrar_Game(f"Jogador que acertou: {vencedor}")

    elif resultado == "LOST":
        mostrar_Game("Resultado: DERROTA!")
        mostrar_Game("Os jogadores ficaram sem vidas.")

    elif resultado == "ABORTED":
        motivos = {
            "host_shutdown": "O host encerrou a partida.",
            "no_players": "Todos os jogadores saíram.",
        }
        motivo = mensagem.get("reason", "unknown")
        mostrar_Game("Resultado: PARTIDA ABORTADA")
        mostrar_Game(f"Motivo: {motivos.get(motivo, motivo)}")

    mostrar_Game(f"Palavra secreta: {palavra.upper()}")
    mostrar_Game("========== RANKING ==========")

    for jogador, pontos in pontuacoes.items():
        mostrar_Game(f"  {jogador}: {pontos} pontos")

    mostrar_Game("========================================")


# Mostra o jogador que perdeu a vez por timeOut
def mostra_timeOut(player_id: str) -> None:
    mostrar_Game(f"O tempo de {player_id} acabou! Turno perdido.")


# Mostra o jogador que perdeu a conexão
def mostrar_desconexao(player_id: str) -> None:
    mostrar_Host(f"{player_id} perdeu a conexão com a partida.")


# Mostra o jogador que perdeu a conexão, conseguiu voltar ao jogo
def mostrar_reconexao(player_id: str) -> None:
    mostrar_Host(f"{player_id} reconectou-se à partida.")


# Mostra as partidas encontradas e enviadas pela mensagem GAME_LIST
def mostrar_partidas(partidas: dict[str, dict[str, Any]]) -> None:

    if not partidas:
        mostrar_Game("Nenhuma partida encontrada.")
        return

    mostrar_Game("========== PARTIDAS ENCONTRADAS ==========")

    for host_id, partida in partidas.items():
        mostrar_Game(f"Host: {host_id}    ID: {partida['game_id']}    Estado: {partida['status']}")
        mostrar_Game(f"Jogadores: {len(partida['players'])}/{partida['max_players']}")
        mostrar_Game(f"Vidas: {partida['lives']}    Tamanho da palavra: {partida['word_length']}")
        mostrar_Game("-----------------------------------------")

    mostrar_Game("Para entrar, utilize /join <host_peer_id>")
