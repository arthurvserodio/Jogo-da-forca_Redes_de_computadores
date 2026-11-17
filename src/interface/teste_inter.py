import time
from typing import cast

from src.config.carrega_config_jogo import carregar_config_jogo
from src.game.forca.gameHost import GameHost
from src.game.forca.gamePlayer import (
    GameOverMessage,
    GamePlayer,
    GameStartMessage,
    StateMessage,
)
from src.game.lobby.lobby import Lobby
from src.interface.cli import interpretar_comando
from src.interface.executar import (
    executar_comando,
    mostra_gameOver,
    mostra_status_jogo,
    mostrar_partidas,
)

config = carregar_config_jogo()

host = GameHost("alice@CIC", config)

# Testar criação
args = interpretar_comando("/create banana 2")
if args is not None:
    executar_comando(args, host, config)

# Testar tentativa de iniciar sem jogadores
args = interpretar_comando("/start")
if args is not None:
    executar_comando(args, host, config)

# Simular entrada de jogador
host.adicionar_jogador("bob@CIC")

# Testar início da partida
args = interpretar_comando("/start")
if args is not None:
    executar_comando(args, host, config)

# Testar status
args = interpretar_comando("/status")
if args is not None:
    executar_comando(args, host, config)


print("\n===== TESTANDO JOGADAS =====")

# Bob tenta uma letra correta
resultado = host.processar_jogada("bob@CIC", "letter", "a")
print("Resultado da jogada:", resultado)

# Mostrar estado atualizado
status = host.obter_status()
if status is not None:
    mostra_status_jogo(status, config)

# Bob tenta uma letra incorreta
resultado = host.processar_jogada("bob@CIC", "letter", "z")
print("Resultado da jogada:", resultado)

# Mostrar estado atualizado
status = host.obter_status()
if status is not None:
    mostra_status_jogo(status, config)


print("\n===== TESTANDO GUESS_RESULT =====")

# Criando um jogador para simular o recebimento
player = GamePlayer("bob@CIC")

# Simulando entrada e início da partida
assert host.game_id is not None
player.entrar_Partida(host.game_id, host.host_id)

game_start = host.gerar_gameStart()
if game_start is not None:
    player.receber_gameStart(cast(GameStartMessage, game_start))

# Simulando o STATE mais recente
state = host.obter_UltimoEstado()

if state is not None:
    player.atualizaState(cast(StateMessage, state))

# Bob tenta uma letra correta
resultado = host.processar_jogada("bob@CIC", "letter", "n")

# Host gera a resposta
resposta = host.gerar_guessResult(resultado)

# Player recebe a resposta
player.receber_guessResult(resposta)


print("\n===== TESTANDO GAME_OVER =====")

# Bob tenta a última letra da palavra
resultado = host.processar_jogada("bob@CIC", "letter", "b")

print("Resultado da última jogada:", resultado)

# Verificar estado final do host
print("Estado final:", host.game_state.name)
print("Resultado:", host.resultado)
print("Vencedor:", host.vencedor)
print("Pontuação:", host.pontuacao)

# Gerar a mensagem GAME_OVER
mensagem_game_over = host.gerar_gameOver()

if mensagem_game_over is not None:
    # Simular recebimento pelo jogador
    recebido = player.receber_gameOver(cast(GameOverMessage, mensagem_game_over))

    print("GAME_OVER recebido:", recebido)

    if recebido is True:
        mostra_gameOver(mensagem_game_over)

    elif recebido == "host cheated: hash mismatch":
        print("Erro: o hash da palavra não corresponde!")

print("\n===== TESTANDO GAME_OVER - DERROTA =====")

# Nova partida independente do teste anterior
host_derrota = GameHost("alice@CIC", config)

host_derrota.criar_jogo("banana", config["lives"], 2)
host_derrota.adicionar_jogador("bob@CIC")
host_derrota.iniciar_jogo()

# Criando o jogador
player_derrota = GamePlayer("bob@CIC")
assert host_derrota.game_id is not None
player_derrota.entrar_Partida(host_derrota.game_id, host_derrota.host_id)

# Simulando GAME_START
game_start = host_derrota.gerar_gameStart()

if game_start is not None:
    player_derrota.receber_gameStart(cast(GameStartMessage, game_start))

# Simulando o STATE inicial
state = host_derrota.obter_UltimoEstado()

if state is not None:
    player_derrota.atualizaState(cast(StateMessage, state))

# Seis palpites incorretos
letras_erradas = ["z", "x", "q", "w", "y", "k"]

assert host_derrota.forca is not None

for letra in letras_erradas:
    resultado = host_derrota.processar_jogada("bob@CIC", "letter", letra)

    print(f"Palpite '{letra}': {resultado}")

    print(f"Vidas restantes: {host_derrota.forca.vidas}")

# Verificar encerramento
print("Estado final:", host_derrota.game_state.name)
print("Resultado:", host_derrota.resultado)

# Gerar GAME_OVER
mensagem_game_over = host_derrota.gerar_gameOver()

if mensagem_game_over is not None:
    recebido = player_derrota.receber_gameOver(cast(GameOverMessage, mensagem_game_over))

    print("GAME_OVER recebido:", recebido)

    if recebido is True:
        mostra_gameOver(mensagem_game_over)


print("\n===== TESTANDO ABORTED - OPEN =====")

host_cancel = GameHost("alice@CIC", config)
host_cancel.criar_jogo("banana", config["lives"], 2)
host_cancel.adicionar_jogador("bob@CIC")

player_cancel = GamePlayer("bob@CIC")
assert host_cancel.game_id is not None
player_cancel.entrar_Partida(host_cancel.game_id, host_cancel.host_id)

# Cancelar antes de iniciar
sucesso = host_cancel.cancelar_jogo()

print("Cancelamento:", sucesso)
print("Estado:", host_cancel.game_state.name)
print("Resultado:", host_cancel.resultado)

mensagem = host_cancel.gerar_gameOver()

if mensagem is not None:
    print("Motivo:", mensagem.get("reason"))
    recebido = player_cancel.receber_gameOver(cast(GameOverMessage, mensagem))
    print("GAME_OVER recebido pelo jogador:", recebido)
    mostra_gameOver(mensagem)

print("\n===== TESTANDO ABORTED - RUNNING =====")

host_running = GameHost("alice@CIC", config)
host_running.criar_jogo("banana", config["lives"], 2)
host_running.adicionar_jogador("bob@CIC")
host_running.iniciar_jogo()

player_running = GamePlayer("bob@CIC")
assert host_running.game_id is not None
player_running.entrar_Partida(host_running.game_id, host_running.host_id)

game_start = host_running.gerar_gameStart()
if game_start is not None:
    player_running.receber_gameStart(cast(GameStartMessage, game_start))

# Host cancela durante a partida
sucesso = host_running.cancelar_jogo()

print("Cancelamento:", sucesso)
print("Estado:", host_running.game_state.name)
print("Resultado:", host_running.resultado)

mensagem = host_running.gerar_gameOver()

if mensagem is not None:
    recebido = player_running.receber_gameOver(cast(GameOverMessage, mensagem))

    print("GAME_OVER recebido pelo jogador:", recebido)

    if recebido is True:
        mostra_gameOver(mensagem)

print("\n===== TESTANDO JOIN_OK =====")

# Criar uma partida
host_join = GameHost("alice@CIC", config)
host_join.criar_jogo("banana", config["lives"], 2)

# Criar o jogador
player_join = GamePlayer("bob@CIC")

# Criar os lobbies dos dois peers
lobby_host = Lobby(host_join, None)
lobby_player = Lobby(None, player_join)

# Bob solicita entrada
mensagem_join = {"type": "JOIN", "game_id": host_join.game_id, "src": "bob@CIC"}

# Host processa a solicitação
resposta = lobby_host.processar_JOIN(mensagem_join)

print("Resposta do host:", resposta)

# Bob recebe JOIN_OK
recebido = lobby_player.recebe_JoinOk({**resposta, "src": "alice@CIC"})

print("JOIN_OK recebido:", recebido)
print("Estado do jogador:", player_join.estado.name)
print("Jogadores no host:", host_join.players)

print("\n===== TESTANDO JOIN_ERR - PARTIDA CHEIA =====")

# Adicionar Carol para completar a partida
host_join.adicionar_jogador("carol@CIC")

# Dave tenta entrar
mensagem_join_dave = {"type": "JOIN", "game_id": host_join.game_id, "src": "dave@CIC"}

resposta_erro = lobby_host.processar_JOIN(mensagem_join_dave)

print("Resposta do host:", resposta_erro)

# Dave recebe a recusa
player_dave = GamePlayer("dave@CIC")
lobby_dave = Lobby(None, player_dave)

recebido = lobby_dave.recebe_JoinErr(resposta_erro)

print("JOIN_ERR recebido:", recebido)
print("Estado de Dave:", player_dave.estado.name)
print("Jogadores no host:", host_join.players)

print("\n===== TESTANDO LEAVE_OK =====")

# Bob solicita saída da partida
mensagem_leave = lobby_player.mensagemLEAVE()

print("Mensagem enviada por Bob:", mensagem_leave)

if mensagem_leave is not None:
    # Simula o envelope recebido pelo host
    mensagem_leave["src"] = "bob@CIC"

    # Host processa a saída
    resposta_leave = lobby_host.processa_Leave(mensagem_leave)

    print("Resposta do host:", resposta_leave)

    if resposta_leave is not None:
        # Bob recebe a confirmação
        recebido = lobby_player.recebe_LeaveOK(resposta_leave)

        print("LEAVE_OK recebido:", recebido)
        print("Estado de Bob:", player_join.estado.name)
        print("Game ID de Bob:", player_join.game_id)
        print("Jogadores restantes:", host_join.players)

print("\n===== TESTANDO REJOIN =====")

# Criar uma partida nova
host_rejoin = GameHost("alice@CIC", config)
host_rejoin.criar_jogo("banana", config["lives"], 2)

host_rejoin.adicionar_jogador("bob@CIC")
host_rejoin.adicionar_jogador("carol@CIC")
host_rejoin.iniciar_jogo()

# Criar Bob e simular entrada na partida
player_rejoin = GamePlayer("bob@CIC")
assert host_rejoin.game_id is not None
player_rejoin.entrar_Partida(host_rejoin.game_id, host_rejoin.host_id)

# Simular GAME_START e STATE
game_start = host_rejoin.gerar_gameStart()

if game_start is not None:
    player_rejoin.receber_gameStart(cast(GameStartMessage, game_start))

state = host_rejoin.obter_UltimoEstado()

if state is not None:
    player_rejoin.atualizaState(cast(StateMessage, state))

# Bob faz uma jogada e ganha 3 pontos
resultado = host_rejoin.processar_jogada("bob@CIC", "letter", "a")

print("Resultado da jogada:", resultado)
print("Pontuação antes da queda:", host_rejoin.pontuacao)

# Simular desconexão
resultado_saida = host_rejoin.remover_jogador("bob@CIC", "disconnect")

print("Resultado da desconexão:", resultado_saida)
print("Jogadores conectados:", host_rejoin.players)
print("Jogadores desconectados:", host_rejoin.jogadores_desconectados)

# Criar os lobbies
lobby_host_rejoin = Lobby(host_rejoin, None)
lobby_player_rejoin = Lobby(None, player_rejoin)

# Bob solicita reconexão
mensagem_join = {"type": "JOIN", "game_id": host_rejoin.game_id, "src": "bob@CIC"}

resposta = lobby_host_rejoin.processar_JOIN(mensagem_join)

print("Resposta do host:", resposta)

# Simular o envelope enviado pelo host
resposta["src"] = "alice@CIC"

recebido = lobby_player_rejoin.recebe_JoinOk(resposta)

print("REJOIN recebido:", recebido)
print("Estado de Bob:", player_rejoin.estado.name)
print("Jogadores conectados:", host_rejoin.players)
print("Pontuação após reconexão:", host_rejoin.pontuacao)

print("\n===== TESTANDO TIMEOUT =====")

# Criar uma nova partida
host_timeout = GameHost("alice@CIC", config)
host_timeout.criar_jogo("banana", config["lives"], 2)

# Adicionar dois jogadores
host_timeout.adicionar_jogador("bob@CIC")
host_timeout.adicionar_jogador("carol@CIC")
host_timeout.iniciar_jogo()

print("Turno inicial:", host_timeout.turno_atual)

# Simular que o tempo de Bob já acabou
host_timeout.inicio_turno = time.monotonic() - host_timeout.turno_timeout - 1

# Verificar timeout
jogador_timeout = host_timeout.verifica_timeout()

print("Jogador que perdeu o turno:", jogador_timeout)
print("Novo turno:", host_timeout.turno_atual)
print("Última jogada:", host_timeout.ultima_jogada)

# Verificar novo STATE
state = host_timeout.obter_UltimoEstado()

if state is not None:
    print("STATE gerado:", state)
    print("Número de sequência:", state["seq"])

# Confirmar comportamento
assert jogador_timeout == "bob@CIC"
assert host_timeout.turno_atual == "carol@CIC"
assert state is not None
assert state["last_guess"] == {"player": "bob@CIC", "timeout": True}

print("TESTE DE TIMEOUT PASSOU!")

print("\n===== TESTANDO GAME_LIST_OK =====")

# Criar uma partida hospedada por Alice
host_games = GameHost("alice@CIC", config)
host_games.criar_jogo("banana", config["lives"], 2)

# Criar o lobby de Alice
lobby_host_games = Lobby(host_games, None)

# Criar o lobby de Bob
player_games = GamePlayer("bob@CIC")
lobby_player_games = Lobby(None, player_games)

# Bob solicita a lista de partidas
solicitacao = lobby_player_games.gerar_mensagem_GAMELIST()

print("Solicitação:", solicitacao)

# Alice gera a resposta
resposta = lobby_host_games.GameList_Ok()

print("Resposta:", resposta)

# Bob recebe e armazena a resposta
recebido = lobby_player_games.recebe_GAMELIST_Ok(resposta)

print("GAME_LIST_OK recebido:", recebido)

# Mostrar partidas encontradas
mostrar_partidas(lobby_player_games.partidas_encontradas)

# Validar resultados
assert recebido is True
assert "alice@CIC" in lobby_player_games.partidas_encontradas
assert lobby_player_games.partidas_encontradas["alice@CIC"]["status"] == "OPEN"

print("TESTE GAME_LIST_OK PASSOU!")


print("\n===== TESTANDO CASOS EXCEPCIONAIS =====")

# 1. JOIN em partida inexistente
resposta = lobby_host_games.processar_JOIN(
    {"type": "JOIN", "game_id": "partida_inexistente", "src": "dave@CIC"}
)

assert resposta["type"] == "JOIN_ERR"
assert resposta["reason"] == "unknown_game"
print("JOIN inválido: OK")


# 2. Palpite fora do turno
host_erro = GameHost("alice@CIC", config)
host_erro.criar_jogo("banana", config["lives"], 2)
host_erro.adicionar_jogador("bob@CIC")
host_erro.adicionar_jogador("carol@CIC")
host_erro.iniciar_jogo()

# Bob começa, mas Carol tenta jogar
resultado = host_erro.processar_jogada("carol@CIC", "letter", "a")

assert resultado["aceito"] is False
assert resultado["erro"] == "not_your_turn"
assert host_erro.turno_atual == "bob@CIC"
print("Palpite fora do turno: OK")


# 3. STATE duplicado
player_erro = GamePlayer("bob@CIC")
assert host_erro.game_id is not None
player_erro.entrar_Partida(host_erro.game_id, host_erro.host_id)

game_start = host_erro.gerar_gameStart()
assert game_start is not None
player_erro.receber_gameStart(cast(GameStartMessage, game_start))

state = host_erro.obter_UltimoEstado()
assert state is not None

primeiro = player_erro.atualizaState(cast(StateMessage, state))
segundo = player_erro.atualizaState(cast(StateMessage, state))

assert primeiro is True
assert segundo is False
print("STATE duplicado: OK")


# 4. GAME_OVER com hash incorreto
host_erro.cancelar_jogo()
mensagem = host_erro.gerar_gameOver()
assert mensagem is not None

mensagem_adulterada = {**mensagem, "word": "laranja"}

resultado_hash = player_erro.receber_gameOver(cast(GameOverMessage, mensagem_adulterada))

assert resultado_hash == "host cheated: hash mismatch"
assert player_erro.estado.name == "PLAYING"
print("GAME_OVER com hash incorreto: OK")

print("\nTODOS OS TESTES EXCEPCIONAIS PASSARAM!")
