import random
from src.game.forca.gameHost import GameHost
from src.network.rendezvous.importConfig.carregaConfig import carregaConfig
from src.network.rendezvous.funcionalidades.funcoes import descobrir_peers

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
        print("Consultando estado da partida...")
        # Futuramente: consultar estado local

    # COMANDOS DE REDE
    #Executando /peers
    elif comando == "/peers":
        filtro = args["filtro"]
        print(f"Consultando peers. Filtro: {filtro}")

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
        print(f"Alterando nível de log para: {nivel}")