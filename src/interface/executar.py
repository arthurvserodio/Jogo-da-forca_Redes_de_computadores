import logging
import random

from src.interface.cli import mostrar_Game
from src.network.rendezvous.funcionalidades.funcoes import descobrir_peers


def executar_comando(args,game_host,config,lobby=None):
    comando = args['comando']
    #COMANDO DO HOST
    #Executar o /create
    if comando ==  '/create':
        #Se for --random
        if args['random']:
            #Pega uma palavra do arquivo word
            with open('words.txt', encoding='utf-8') as arquivo:
                conteudo = arquivo.read()
                list_palavra = conteudo.split()
                palavra = random.choice(list_palavra) #random choice para pegar uma palavra aleatoria
        else:
            palavra = args['palavra']

         # Obtém a quantidade máxima de jogadores
        max_players = args['max_players']
        sucesso = game_host.criar_jogo(palavra,config['lives'],max_players)
        if sucesso:
            print(f"Partida criada! ID: {game_host.game_id} palavra: {palavra} máximo de jogadores: {game_host.max_players}")
        else:
            print("Não foi possível criar a partida.")
    #Executar o /start
    elif comando == '/start':
        sucesso = game_host.iniciar_jogo()
        if sucesso:
            print("Partida iniciada!")
        else:
            print("Não foi possível iniciar a partida.")
    #Executar o /cancel
    elif comando == '/cancel':
        sucesso = game_host.cancelar_jogo()
        if sucesso:
            print("Partida cancelada!")
        else:
            print("Não foi possível cancelar a partida.")

    #COMANDO DO LOOBY
    #Executar o /games
    elif comando == '/games': 
        #Se não existir nada, não pode fazer nada
        if lobby is None:
            return None
        #Solicita ao lobby a criação da mensagem GAME_LIST
        mensagem = lobby.gerar_mensagem_GAMELIST()
        mostrar_Game("Consultando partidas disponíveis...")
        # Devolve a mensagem para a camada de comunicação
        return mensagem

    #Executar o /join
    elif comando == '/join':
        #Se não existir nada, não pode fazer nada
        if lobby is None:
            return None
        host_id = args["host_peer_id"]
        #Busca partida hospedada por esse host
        partida = lobby.partidas_encontradas.get(host_id)
        #Se a partida não foi encontrada para esse host ou ela não está em OPEN, não tem como fazer o join
        if partida is None or partida['status'] != 'OPEN':
            mostrar_Game(f"Nenhuma partida aberta encontrada para {host_id}")
            return None

        # Gera a solicitação JOIN
        mensagem = lobby.mensagemJOIN(partida["game_id"])
        mostrar_Game(f"Solicitando entrada na partida de {host_id}")
        return mensagem


    #Executar o /leave
    elif comando == '/leave':
        #Se não existir nada, não pode fazer nada
        if lobby is None:
            return None
        #Gera a mensagem LEAVE
        mensagem = lobby.mensagemLEAVE()
        if mensagem is None:
            mostrar_Game("Você não está participando de nenhuma partida.")
            return None
        mostrar_Game("Solicitando a saída da partida...")
        return mensagem

    #COMANDO DO JOGADOR
    #Executar o /guess ou /word
    elif comando == "/guess" or comando == "/word":
        if lobby is None:
            mostrar_Game("Lobby não disponível.")
            return None
        #Pega o palpite 
        if comando == '/guess':
            palpite = args['letra']
        else:
            palpite = args['palavra']
        mensagem = lobby.game_player.gerar_guess(palpite)
        if mensagem is None:
            mostrar_Game(
            "Não foi possível enviar o palpite. "
            "Verifique se você está jogando e se é sua vez.")

        return mensagem


    #Executar o /status
    elif comando == "/status":
        status = game_host.obter_status()
        #Se não tem nenhuma partida, então o status é None
        if status is None:
            mostrar_Game("Nenhuma partida hospedada")
            return
        if status['estado'] == "OPEN" :
            mostrar_Game(f"Game ID: {status['game_id']}")
            mostrar_Game(f"Estado Atual: {status['estado']}")
            mostrar_Game(f"Jogadores: {len(status['jogadores'])}/{status['max_players']}")
        elif status['estado'] == "RUNNING":
            mostra_status_jogo(status,config)
        else:
            mostrar_Game(f"Estado atual: {status['estado']}")

        # Verifica se o peer está participando de uma partida
        if lobby is not None:
            jogador = lobby.game_player

            if jogador.estado.name == "JOIN":
                mostrar_Game(f"Game ID: {jogador.game_id}")
                mostrar_Game(f"Host: {jogador.host_id}")
                mostrar_Game(f"Estado atual: {jogador.estado.name}")
                # Se já começou, exibe as informações do jogo
            if jogador.estado.name == "PLAYING":
                mostra_status_jogo(status,config)
                return

        mostrar_Game("Você não está em nenhuma partida.")

    # COMANDOS DE REDE
    #Executando /peers
    elif comando == "/peers":
        filtro = args["filtro"]
        #Consulta os peers no rendezvous
        peers = descobrir_peers()
        peers_filter = []
        #Se retornou None é pq deu errado
        if peers is None:
            print("Não foi possível consultar os peers")
            return
        #Filtra por namespace
        if filtro is not None and filtro != "*":
            namespace = filtro[1:]
            #Só coloca em peers filtrados aqueles que tem o namespace desejado
            for peer in peers:
                if peer["namespace"] == namespace:
                    peers_filter.append(peer)
        else:
            peers_filter = peers.copy()
        
        if len(peers_filter) == 0:
            print("Nenhum peer encontrado.")
            return

        # Exibe os peers
        print("Peers disponíveis:")
        for peer in peers_filter:
            print(f"- {peer['name']}@{peer['namespace']} "
                f"({peer['ip']}:{peer['port']})") 

    #Executando /conn
    elif comando == "/conn":
        print("Consultando conexões ativas...")

    #Executando /rtt
    elif comando == "/rtt":
        print("Consultando RTT dos peers...")

    #Executando /reconnect
    elif comando == "/reconnect":
        print("Solicitando reconexão...")

    # CONFIGURAÇÕES
    #Executando /log
    elif comando == "/log":
        nivel = args["nivel"]
        logging.getLogger().setLevel(getattr(logging, nivel))
        print(f"Nível de log alterado para {nivel}")
        logging.debug("Teste DEBUG")
        logging.info("Teste INFO")
        logging.warning("Teste WARNING")
        logging.error("Teste ERROR")

#Status do jogo RUNNING - Mostra quando dá /status ou muda STATE
def mostra_status_jogo(status,config):
    mostrar_Game(f'{status['game_id']}  (host: {status['host_id']})  status: {status['estado']}')
    mostrar_Game(f'Palavra: {status['palavra_mask']}     Vidas: {status['vidas']} / {config['lives']}     Erradas: {", ".join(status['letras_erradas'])}')
    mostrar_Game(f'Jogadores: {", ".join(status['jogadores'])}   Vez de: {status['turno_atual']}')