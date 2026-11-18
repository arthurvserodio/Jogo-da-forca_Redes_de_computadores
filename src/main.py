import logging

from ipaddress import ip_address
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Any, cast

from pydantic import ValidationError

from src.utils.logger import configurar_logs
from src.config.carrega_config_jogo import carregar_config_jogo
from src.config.loader import ConfigLoader
from src.domain.peer import Peer, PeerAddress
from src.game.forca.gameHost import GameHost
from src.game.forca.gamePlayer import GamePlayer
from src.game.lobby.lobby import Lobby
from src.game.roteador_jogo import RoteadorJogo
from src.interface.cli import interpretar_comando, mostrar_ajuda
from src.interface.executar import executar_comando
from src.network.connection.manager import ConnectionManager
from src.network.connection.peer_table import PeerTable
from src.network.rendezvous.RendezvousManeger import RendezvousManeger


logger = logging.getLogger(__name__)
# Conectar com os peers que foram descobertos
def conectar_descobertos(
    rede: ConnectionManager, 
    rendezvous: RendezvousManeger, 
    peer_table: PeerTable,
    discovery_lock: Lock,
    ) -> None:
    with discovery_lock:
        # Descobre os Peers e faz conexão
        resposta = rendezvous.descobrir_peers()
        if resposta is None or resposta.get("status") != "OK":
            print("[REDE] Falha ao descobrir peers no Rendezvous")
            return
        ips_teste = {
            "grupo8COPIA@CIC": "192.168.0.188",  # Debian
            "grupo8TESTE@CIC": "192.168.0.114",       # Segundo peer Windows
        }
        for encontrado in rendezvous.peers:
            dados = cast(dict[str, Any], encontrado)
            # Informações para realizar a conexão
            nome = dados.get("name")
            namespace = dados.get("namespace")
            endereco_ip = dados.get("ip")
            porta = dados.get("port", dados.get("listen_port"))
            #Se o nome ou namespace não for string, não pode ser realizado a conexão
            if not isinstance(nome, str) or not isinstance(namespace, str):
                print(f"[REDE] Registro inválido: {dados!r}")
                continue
            peer_id = f"{nome}@{namespace}"
            #Se o IP não for string e a porta um inteiro, também não pode conectar
            if not isinstance(endereco_ip, str) or not isinstance(porta, int):
                print(f"[REDE] {peer_id} descoberto sem IP/porta: {dados!r}")
                continue
            try:
                # Utilizar o IP local do Debian apenas para testes.
                # IPs utilizados apenas nos testes locais
                if peer_id in ips_teste:
                    endereco_ip = ips_teste[peer_id]
                peer = Peer(
                    name=nome,
                    namespace=namespace,
                    address=PeerAddress(
                        ip=ip_address(endereco_ip),
                        port=porta,
                    ),
                )
                # Registrar antes de iniciar o handshake
                peer_table.add_or_update(peer)
                rede.connect(peer)
            except (OSError, ValueError) as erro:
                logger.debug("Não foi possível conectar a %s: %s", peer_id, erro)

# Usado para descobrir peers periodicamente
def descoberta_periodica(
    rede: ConnectionManager,
    rendezvous: RendezvousManeger,
    peer_table: PeerTable,
    discovery_lock: Lock,
    parar: Event,
    intervalo: int,
) -> None:
    # wait() permite interromper imediatamente ao executar /quit.
    while not parar.wait(intervalo):
        conectar_descobertos(rede, rendezvous, peer_table, discovery_lock)

# Monitora os turnos do jogo, verificação de timeOut
def monitorar_turnos(
    roteador: RoteadorJogo,
    parar: Event,
) -> None:
    # Verifica a cada segundo, sem bloquear a CLI.
    while not parar.wait(1.0):
        roteador.verificar_timeout_turno()

def main() -> None:
    # Carregar as configurações
    project_root = Path(__file__).parent.parent
    file_path = project_root / "config.json"

    try:
        settings = ConfigLoader(file_path).load()

    # Validar as configurações
    except ValidationError as error:
        # TODO: Passar os erros para o sistema de logs
        print("Configuração inválida")
        for detail in error.errors():
            field = ".".join(str(part) for part in detail["loc"])
            print(f"- {field or 'arquivo de configurações'}: {detail['msg']}")
        return

    except (OSError, UnicodeError) as error:
        print("Não foi possível ler arquivo de configurações: ", error)
        return
    # Configurando o logger
    caminho_log = (
        project_root / settings.log_file
        if settings.log_file is not None
        else project_root / "logs" / "pyp2p-forca.log"
    )
    configurar_logs(caminho_log, nivel_console="ERROR")
    logger.info("Iniciando PyP2P-Forca")

    config = carregar_config_jogo()
    # ID do peer
    peer_id = f"{settings.name}@{settings.namespace}"

    # Criar Peer Local
    local_peer = Peer(
        name=str(settings.name),
        namespace=str(settings.namespace),
        address=PeerAddress(
            ip=ip_address("127.0.0.1"),
            port=settings.listen_port,
        ),
    )
    # Criar PeerTable (banco de dados)
    peer_table = PeerTable()
    # Componentes do jogo
    game_host = GameHost(peer_id, config)
    game_player = GamePlayer(peer_id)
    lobby = Lobby(game_host, game_player)
    # Roteador de mensagens do jogo
    roteador = RoteadorJogo(lobby,config)
    # Criar o ConnectionManager
    rede = ConnectionManager(
        local_peer=local_peer,
        peer_table=peer_table,
        on_message=roteador.receber_mensagem,
        ping_interval=config["ping_interval"],
        ping_miss_limit=config["ping_miss_limit"],
        on_disconnect=roteador.tratar_desconexao,
        on_reconnect=roteador.tratar_reconexao,
        max_reconnect_attempts=config["max_reconnect_attempts"],
        base_backoff=config["base_backoff"],
        max_backoff=config["max_backoff"],
    )
    # Conecta o roteador à rede
    roteador.conectar_rede(rede)
    # Therad de turnos rodando
    parar_turnos = Event()
    thread_turnos = Thread(
        target=monitorar_turnos,
        args=(roteador, parar_turnos),
        name="game-turn-timeout",
        daemon=True,
    )
    thread_turnos.start()
    # Gerenciador do rendezvous
    rendezvous = RendezvousManeger(config)
    discovery_lock = Lock()
    parar_descoberta = Event()
    thread_descoberta: Thread | None = None
    try:
        # Inicia o servidor TCP
        rede.start()
        resposta = rendezvous.registrar()
        if resposta is not None and resposta.get("status") == "OK":
            print("[REDE] Registrado no Rendezvous")
            rendezvous.refresh_peer(resposta)
            # Descobre os peers presentes e se conecta a eles
            conectar_descobertos(rede, rendezvous, peer_table, discovery_lock)
            thread_descoberta = Thread(
                target=descoberta_periodica,
                args=(
                    rede,
                    rendezvous,
                    peer_table,
                    discovery_lock,
                    parar_descoberta,
                    settings.discover_interval,
                ),
                name="rdv-discover",
                daemon=True,
            )
            thread_descoberta.start()
        else:
            erro = resposta.get("message") if resposta is not None else "sem resposta"
            print(f"[REDE] Falha no registro: {erro}")
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
                comando = args["comando"]
                # Comando /help
                if comando == "/help":
                    mostrar_ajuda()
                    continue
                # Comando /quit
                if comando == "/quit":
                    with roteador.host_lock:
                        if game_host.game_state.name in ("OPEN", "RUNNING"):
                            roteador.cancelar_partida()
                    print("Encerrando o programa...")
                    break
                elif comando == "/reconnect":
                    rede.reset_reconnect()
                    conectar_descobertos(rede, rendezvous, peer_table, discovery_lock)
                elif comando == "/conn":
                    print("[REDE] Conexões:", rede.connected_peer_list())
                elif comando == "/rtt":
                    rtts = rede.get_rtt()

                    if not rtts:
                        print("[REDE] Nenhum peer conectado.")
                    else:
                        for peer_id, rtt in rtts.items():
                            if rtt == 0:
                                print(f"[REDE] {peer_id}: RTT ainda não medido")
                            else:
                                print(f"[REDE] {peer_id}: RTT médio = {rtt:.2f} ms")

                elif comando == "/games":
                    roteador.solicitar_partidas()
                elif comando == "/join":
                    roteador.entrar_partida(args["host_peer_id"])
                elif comando == "/guess":
                    roteador.enviar_palpite(args["letra"])
                elif comando == "/cancel":
                    roteador.cancelar_partida()

                elif comando == "/word":
                    roteador.enviar_palpite(args["palavra"])

                elif comando == "/leave":
                    roteador.enviar_leave()
                #Comando do Host
                elif comando == "/start":
                    roteador.iniciar_partida()
                    
                else:
                    # Comandos que consultam ou modificam o GameHost compartilham o lock com as threads TCP e de timeout.
                    if comando in {"/create", "/cancel", "/status"}:
                        with roteador.host_lock:
                            executar_comando(args, game_host, config, lobby, rendezvous)
                    else:
                        executar_comando(args, game_host, config, lobby, rendezvous)

            except (ValueError, RuntimeError, OSError) as erro:
                print(f"[CLI] Não foi possível executar o comando: {erro}")
            except (EOFError, KeyboardInterrupt):
                print("\nEncerrando o programa...")
                break
    finally:
        parar_descoberta.set()
        parar_turnos.set()
        thread_turnos.join()
        logger.info("Encerrando aplicação")
        if thread_descoberta is not None:
            thread_descoberta.join()
        # Fecha primeiro as conexões; depois remove o anúncio no Rendezvous.
        rede.stop()
        if rendezvous.registrado:
            # Rotina de fechamento
            rendezvous.desregistrar()
        logger.info("Aplicação encerrada")


if __name__ == "__main__":
    main()
