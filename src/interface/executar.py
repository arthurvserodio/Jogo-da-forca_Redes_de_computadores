import random
import logging
from src.game.forca.gameHost import GameHost
from src.network.rendezvous.importConfig.carregaConfig import carregaConfig
from src.network.rendezvous.funcionalidades.funcoes import descobrir_peers
from src.interface.cli import mostrar_Game
from src.game.fsm.MaqEstadosJogo import MaqEstadosJogo

def executar_comando(args,game_host,config):
    comando = args['comando']
    #COMANDO DO HOST
    #Executar o /create
    if comando ==  '/create':
        #Se for --random
        if args['random']:
            #Pega uma palavra do arquivo word
            with open('words.txt', 'r', encoding='utf-8') as arquivo:
                conteudo = arquivo.read()
                list_palavra = conteudo.split()
                palavra = random.choice(list_palavra) #random choice para pegar uma palavra aleatoria
        else:
            palavra = args['palavra']

        sucesso = game_host.criar_jogo(palavra,config['lives'])
        if sucesso:
            print(f"Partida criada! ID: {game_host.game_id} palavra: {palavra}")
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
        print("Solicitando lista de partidas")
        #Conectar com o LOBBY

    #Executar o /join
    elif comando == '/join':
        host_id = args["host_peer_id"]
        print(f"Solicitando entrada na partida de {host_id}")
        #Conectar com o looby

    #Executar o /leave
    elif comando == '/leave':
        print("Solicitando a saída da partida")
        #Conectar com o looby

    #COMANDO DO JOGADOR
    #Executar o /guess
    elif comando == "/guess":
        letra = args['letra']
        print(f"Enviando palpite de letra: {letra}")
        # Futuramente: encaminhar palpite ao GamePlayer

    #Executar o /word
    elif comando == "/word":
        palavra = args["palavra"]
        print(f"Enviando palpite de palavra: {palavra}")
        # Futuramente: encaminhar palpite ao GamePlayer

    #Executar o /status
    elif comando == "/status":
        status = game_host.obter_status()
        #Se não tem nenhuma partida, então o status é None
        if status == None:
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

    # COMANDOS DE REDE
    #Executando /peers
    elif comando == "/peers":
        filtro = args["filtro"]
        #Consulta os peers no rendezvous
        peers = descobrir_peers()
        peers_filter = []
        #Se retornou None é pq deu errado
        if peers == None:
            print("Não foi possível consultar os peers")
            return
        #Filtra por namespace
        if filtro != None and filtro != "*":
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