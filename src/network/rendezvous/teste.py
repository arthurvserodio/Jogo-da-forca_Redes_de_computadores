import time
from threading import Lock
from typing import cast
from unittest.mock import patch

from src.network.rendezvous.importConfig.carregaConfig import carregaConfig
from src.network.rendezvous.RendezvousManeger import RendezvousManeger
from src.network.rendezvous.types import Config


def main() -> None:
    config = {
        "rdv_host": "localhost",
        "rdv_port": 8080,
        "namespace": "CIC",
        "name": "alice",
        "listen_port": 8081,
        "register_ttl": 7200,
    }

    manager = RendezvousManeger(cast(Config, config))

    # Simula respostas do servidor sem usar a rede
    respostas = iter(
        [
            {"status": "OK", "ttl": 7200, "ip": "127.0.0.1", "port": 8081},
            {
                "status": "OK",
                "peers": [
                    {"name": "alice", "namespace": "CIC"},
                    {"name": "bob", "namespace": "CIC"},
                ],
            },
            {"status": "OK"},
        ]
    )

    mocker = patch.object(manager, "connectServer", side_effect=respostas)
    mock_connect = mocker.start()

    # TESTE 1 - REGISTER
    resposta = manager.registrar()

    assert resposta is not None
    assert resposta["status"] == "OK"
    assert manager.registrado is True
    print("Teste 1: REGISTER OK")

    # TESTE 2 - DISCOVER
    resposta = manager.descobrir_peers()

    assert resposta is not None
    assert resposta["status"] == "OK"
    assert manager.peers == [{"name": "bob", "namespace": "CIC"}]
    print("Teste 2: DISCOVER OK")

    # TESTE 3 - UNREGISTER
    resposta = manager.desregistrar()

    assert resposta is not None
    assert resposta["status"] == "OK"
    assert manager.registrado is False
    print("Teste 3: UNREGISTER OK")

    print("\nTodos os testes básicos passaram!")

    # TESTE 4 - REGISTER com erro
    manager.registrado = False
    mock_connect.side_effect = lambda mensagem: {"status": "ERROR", "message": "Registro recusado"}

    resposta = manager.registrar()

    assert resposta is not None
    assert resposta["status"] == "ERROR"
    assert manager.registrado is False
    print("Teste 4: REGISTER com erro OK")

    # TESTE 5 - Falha de conexão
    mock_connect.side_effect = lambda mensagem: None

    resposta = manager.registrar()

    assert resposta is None
    assert manager.registrado is False
    print("Teste 5: Falha de conexão OK")

    # TESTE 6 - DISCOVER com erro
    manager.peers = [{"name": "bob", "namespace": "CIC"}]

    mock_connect.side_effect = lambda mensagem: {
        "status": "ERROR",
        "message": "Servidor indisponível",
    }

    resposta = manager.descobrir_peers()

    assert resposta is not None
    assert resposta["status"] == "ERROR"

    # O gerenciador mantém a última lista conhecida
    assert manager.peers == [{"name": "bob", "namespace": "CIC"}]

    print("Teste 6: DISCOVER com erro OK")

    # TESTE 7 - UNREGISTER com falha
    manager.registrado = True
    mock_connect.side_effect = lambda mensagem: None

    resposta = manager.desregistrar()

    assert resposta is None
    assert manager.registrado is True

    print("Teste 7: UNREGISTER com falha OK")

    # Criamos outro gerenciador para não interferir nos testes anteriores
    mocker.stop()
    manager_refresh = RendezvousManeger(cast(Config, config))

    contador = [0]
    lock = Lock()

    # Simula o servidor respondendo ao REGISTER
    def servidor_simulado(mensagem: str) -> dict[str, str | int]:
        with lock:
            contador[0] += 1

        return {"status": "OK", "ttl": 1, "ip": "127.0.0.1", "port": 8081}

    mocker_refresh = patch.object(manager_refresh, "connectServer", side_effect=servidor_simulado)
    mocker_refresh.start()

    # TESTE 8 - Renovação automática
    resposta = manager_refresh.registrar()
    assert resposta is not None
    assert manager_refresh.registrado is True

    manager_refresh.refresh_peer(resposta)

    # TTL = 1 segundo; refresh ocorre após aproximadamente 0,8 s
    time.sleep(1.1)

    with lock:
        total = contador[0]

    assert total >= 2
    print("Teste 8: Refresh automático OK")

    # TESTE 9 - Impedir threads duplicadas
    thread_original = manager_refresh.thread_refresh

    manager_refresh.refresh_peer(resposta)

    assert manager_refresh.thread_refresh is thread_original
    print("Teste 9: Sem threads duplicadas OK")

    # TESTE 10 - Encerrar refresh
    manager_refresh.termina_refresh()

    assert manager_refresh.thread_refresh is None
    assert manager_refresh.parar_refresh is None
    assert thread_original is not None
    assert not thread_original.is_alive()

    with lock:
        total_antes = contador[0]

    time.sleep(1.1)

    with lock:
        total_depois = contador[0]

    assert total_antes == total_depois
    print("Teste 10: Encerramento do refresh OK")
    mocker_refresh.stop()


def teste_rendezvous_real() -> None:
    config = carregaConfig()
    manager = RendezvousManeger(config)

    # TESTE 11 - REGISTER real
    resposta = manager.registrar()
    print("Resposta REGISTER:", resposta)

    assert resposta is not None
    assert resposta.get("status") == "OK"
    assert manager.registrado is True
    print("Teste 11: REGISTER real OK")

    try:
        # TESTE 12 - DISCOVER real
        resposta = manager.descobrir_peers()
        print("Resposta DISCOVER:", resposta)

        assert resposta is not None
        assert resposta.get("status") == "OK"
        print("Peers encontrados:", manager.peers)
        print("Teste 12: DISCOVER real OK")

    finally:
        # TESTE 13 - UNREGISTER real
        resposta = manager.desregistrar()
        print("Resposta UNREGISTER:", resposta)

        assert resposta is not None
        assert resposta.get("status") == "OK"
        assert manager.registrado is False
        print("Teste 13: UNREGISTER real OK")


if __name__ == "__main__":
    teste_rendezvous_real()
