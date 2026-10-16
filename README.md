# PyP2P-Forca
Projeto desenvolvido para a disciplina de Redes de Computadores.
A proposta é criar um Jogo da Forca em arquitetura Peer-to-Peer (P2P) utilizando Python e comunicação via sockets TCP.
O projeto utiliza um servidor Rendezvous já disponibilizado pelo professor para registrar e descobrir outros peers na rede.
# Objetivo
Desenvolver um cliente P2P capaz de se comunicar com outros peers e permitir partidas de Jogo da Forca de forma distribuída.
Entre os principais pontos do trabalho estão:
- conexão com o servidor Rendezvous;
- descoberta de outros peers;
- comunicação direta entre peers via TCP;
- troca de mensagens em JSON;
- criação e participação em partidas;
- gerenciamento das conexões entre os participantes.
# Arquitetura
O servidor Rendezvous é responsável apenas pela descoberta inicial dos peers.
Depois da descoberta, a comunicação ocorre diretamente entre os participantes:
```text
              Servidor Rendezvous
                     |
             descoberta de peers
                     |
          -------------------------
          |           |           |
        Peer A      Peer B      Peer C
          \___________|___________/
               conexões TCP
```
Durante uma partida, um dos peers atua temporariamente como host, enquanto os demais participam como jogadores.
# Servidor Rendezvous
Servidor disponibilizado para o trabalho:
Host: pyp2p.mfcaetano.cc
Porta: 8080
Repositório de referência: https://github.com/mfcaetano/pyp2p-rdv
# Autores
- Arthur Vilaça Serodio(matrícula: 251039335)
- João Rafael Rodrigues(matrícula: 251004429)
-  Paulo Henrique Rosa(matrícula: 170163687)
# Disciplina
Redes de Computadores
