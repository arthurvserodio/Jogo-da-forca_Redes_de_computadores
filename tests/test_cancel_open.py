"""Testes de cancelamento OPEN sem abrir sockets TCP reais.

Coloque em tests/test_cancel_open.py e rode:
    python -m pytest tests/test_cancel_open.py -v -s
"""

from types import SimpleNamespace
from typing import Any

import pytest

from src.game.forca.gameHost import GameHost
from src.game.forca.gamePlayer import GamePlayer
from src.game.lobby.lobby import Lobby
from src.game.roteador_jogo import RoteadorJogo


HOST_ID = "host@CIC"
PLAYER_ID = "jogador@CIC"
CONFIG: dict[str, Any] = {
    "lives": 6,
    "max_players": 4,
    "turn_timeout": 30,
    "ping_interval": 30,
    "ping_miss_limit": 3,
}


class RedeSimulada:
    """Substitui apenas o transporte; usa os roteadores reais nas duas pontas."""

    def __init__(self) -> None:
        self.rotas: dict[str, RoteadorJogo] = {}
        self.mensagens: list[tuple[str, dict[str, Any]]] = []
        self.entregar = True

    def send(self, destino: str, mensagem: dict[str, Any]) -> None:
        self.mensagens.append((destino, mensagem.copy()))
        if not self.entregar:
            return
        remetente = mensagem["src"]
        # O roteador usa peer.peer_id para autenticar remetente.
        self.rotas[destino].receber_mensagem(
            SimpleNamespace(peer_id=remetente), mensagem
        )


@pytest.fixture
def partida_aberta() -> tuple[GameHost, GamePlayer, RoteadorJogo, RedeSimulada]:
    host = GameHost(HOST_ID, CONFIG)
    assert host.criar_jogo("banana", 6)["aceito"] is True

    player = GamePlayer(PLAYER_ID)
    assert host.game_id is not None
    assert host.adicionar_jogador(PLAYER_ID) == "join_ok"
    assert player.entrar_Partida(host.game_id, HOST_ID) is True
    assert host.game_state.name == "OPEN"
    assert player.estado.name == "JOINED"

    roteador_host = RoteadorJogo(Lobby(host, GamePlayer(HOST_ID)), CONFIG)
    roteador_player = RoteadorJogo(
        Lobby(GameHost(PLAYER_ID, CONFIG), player), CONFIG
    )
    rede = RedeSimulada()
    rede.rotas = {HOST_ID: roteador_host, PLAYER_ID: roteador_player}
    roteador_host.conectar_rede(rede)  # type: ignore[arg-type]
    roteador_player.conectar_rede(rede)  # type: ignore[arg-type]
    return host, player, roteador_host, rede


def test_cancel_open_envia_game_over_e_retorna_player_para_idle(partida_aberta, capsys):
    host, player, roteador, rede = partida_aberta
    game_id = host.game_id

    roteador.cancelar_partida()

    assert host.game_state.name == "FINISHED"
    envios = [m for destino, m in rede.mensagens if destino == PLAYER_ID]
    assert len(envios) == 1, f"Esperava 1 envio ao jogador, recebi: {envios}"
    mensagem = envios[0]
    assert mensagem["type"] == "GAME_OVER"
    assert mensagem["game_id"] == game_id
    assert mensagem["result"] == "ABORTED"
    assert mensagem["reason"] == "host_shutdown"
    assert mensagem["src"] == HOST_ID
    assert mensagem["dst"] == PLAYER_ID
    assert mensagem["ttl"] == 1
    assert isinstance(mensagem["msg_id"], str)

    assert player.estado.name == "IDLE", (
        f"Player deveria estar IDLE, mas ficou {player.estado.name}. "
        f"Mensagem: {mensagem}"
    )
    assert player.game_id is None
    assert player.host_id is None
    assert "PARTIDA ABORTADA" in capsys.readouterr().out


def test_sem_entrega_player_permanece_joined(partida_aberta):
    """Controle: se a mensagem não chega, o jogador não tem como mudar estado."""
    host, player, roteador, rede = partida_aberta
    rede.entregar = False

    roteador.cancelar_partida()

    assert host.game_state.name == "FINISHED"
    assert len(rede.mensagens) == 1
    assert player.estado.name == "JOINED"
    assert player.game_id is not None
