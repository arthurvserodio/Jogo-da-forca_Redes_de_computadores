# PyP2P-Forca

Projeto desenvolvido para a disciplina de Redes de Computadores.
A proposta é criar um Jogo da Forca em arquitetura Peer-to-Peer (P2P) utilizando Python e comunicação via sockets TCP.
O projeto utiliza um servidor Rendezvous já disponibilizado pelo professor para registrar e descobrir outros peers na rede.

## Objetivo

Desenvolver um cliente P2P capaz de se comunicar com outros peers e permitir partidas de Jogo da Forca de forma distribuída.
Entre os principais pontos do trabalho estão:

- conexão com o servidor Rendezvous;
- descoberta de outros peers;
- comunicação direta entre peers via TCP;
- troca de mensagens em JSON;
- criação e participação em partidas;
- gerenciamento das conexões entre os participantes.

## Arquitetura

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

## Servidor Rendezvous

Servidor disponibilizado para o trabalho:

- Host: `pyp2p.mfcaetano.cc`
- Porta: `8080`
- Repositório de referência: [pyp2p-rdv](https://github.com/mfcaetano/pyp2p-rdv)

## Autores

- Arthur Vilaça Serodio (matrícula: 251039335)
- João Rafael Rodrigues (matrícula: 251004429)
- Paulo Henrique Rosa (matrícula: 170163687)

## Disciplina

Redes de Computadores

## Estado atual

**O jogo completo ainda não está disponível.** `src/main.py` está vazio e o
módulo de conexão TCP entre peers ainda não foi implementado neste clone.
O exemplo executável registra um peer no Rendezvous, inicia a renovação do
registro, consulta outros peers e aguarda Enter para encerrar e remover o registro.
Ele **não abre um servidor TCP local, não conecta aos peers encontrados e não
inicia uma partida**. Uma lista de peers vazia pode ser um resultado normal.

## Mínimo necessário para executar

Para executar o **exemplo atual de Rendezvous** pelo caminho recomendado:

- [ ] **uv 0.11.24 instalado** — gerencia o Python e o ambiente virtual.
  [Instalação oficial para Windows, macOS e Linux](https://docs.astral.sh/uv/getting-started/installation/).
- [ ] **Código do projeto no computador**, incluindo `config.json`,
  `pyproject.toml`, `uv.lock` e `.python-version`. Pode ser obtido por clone
  ou por download e extração do ZIP da branch que contém esses arquivos.
- [ ] **Terminal e editor de texto** para executar os comandos e ajustar
  nome/namespace no `config.json`; os aplicativos do próprio sistema bastam.
- [ ] **Acesso à internet** para a primeira instalação e comunicação com
  `pyp2p.mfcaetano.cc` na porta TCP `8080`.

**Não precisa instalar Python manualmente:** o uv instala o **Python 3.13.12**
indicado em `.python-version` quando necessário. Esse é o Python usado para
execução, mas sua instalação é gerenciada pelo uv.

Na pasta do projeto, depois de ajustar `config.json`:

```sh
uv sync --locked --no-dev
uv run --locked --no-dev python -m src.network.rendezvous.teste
```

`--no-dev` dispensa as ferramentas de desenvolvimento. Atualmente o código de
execução usa apenas a biblioteca padrão do Python, sem bibliotecas externas.
Não é necessário ativar `.venv` nem instalar pacotes por `requirements.txt`.
O jogo completo ainda depende da integração dos módulos descrita acima.

### Opcionais para desenvolvimento

| Ferramenta | Quando é necessária |
| --- | --- |
| Git | Para clonar/atualizar o repositório e usar hooks; dispensável para executar a partir de ZIP |
| GNU Make | Para usar os atalhos `make`; os comandos `uv` funcionam sem ele |
| Ruff, mypy e pre-commit | Para qualidade do código; instalados por `uv sync --locked`, sem `--no-dev` |
| Docker | Para usar a imagem Linux ou o Dev Container |
| VS Code e extensão Dev Containers | Somente para abrir o ambiente de desenvolvimento no container |

Não é necessário instalar uma máquina virtual para executar pelo uv.
Depois de instalar uv, reabra o terminal se ele ainda não reconhecer `uv --version`.

## Início rápido para desenvolvimento

Os comandos seguintes devem ser executados **na raiz do repositório**, onde estão
`pyproject.toml`, `uv.lock` e `config.json`.

```sh
git clone https://github.com/arthurvserodio/Jogo-da-forca_Redes_de_computadores.git
cd Jogo-da-forca_Redes_de_computadores
uv sync --locked
uv run --locked python scripts/check.py
```

Se o projeto já foi clonado, entre nessa pasta e execute os dois últimos comandos.
O clone precisa conter os arquivos de configuração citados: mudanças feitas apenas
na máquina de um integrante só estarão disponíveis aos colegas depois de commit,
push e atualização da branch correspondente.

`uv sync --locked` cria `.venv` e instala as versões de `uv.lock`, inclusive as
ferramentas de desenvolvimento. **Não é necessário ativar `.venv`**: `uv run` usa
esse ambiente automaticamente. `requirements.txt` está vazio e não é o caminho
de instalação deste projeto. Não copie `.venv` de um computador para outro.

## Configuração antes de executar

Edite `config.json`, preservando JSON válido: aspas duplas, sem comentários nem
vírgula depois do último campo. Os campos usados pelo exemplo atual são:

| Campo | Como configurar |
| --- | --- |
| `rdv_host` | `pyp2p.mfcaetano.cc`, servidor fornecido pelo professor |
| `rdv_port` | `8080`, porta do servidor Rendezvous |
| `namespace` | Namespace combinado para a descoberta, por exemplo `CIC` |
| `name` | Nome exclusivo para cada peer dentro desse namespace |
| `listen_port` | Porta anunciada para receber conexões; o exemplo ainda não a abre |
| `register_ttl` | Validade solicitada para o registro, em segundos; padrão `7200` |

O valor versionado de `name` é `grupo8`: altere-o para evitar que todos os colegas
registrem a mesma identidade. A identidade é `name@namespace`; peers que desejam
se descobrir precisam consultar o mesmo namespace. Para futuras instâncias no
mesmo computador, use nomes e portas de escuta diferentes.

Os demais campos do arquivo são destinados aos módulos ainda em desenvolvimento;
sua presença não significa que jogo, logs, keep-alive ou reconexão já funcionem.
O carregador atual não implementa sobrescrita por argumentos de linha de comando.
Evite incluir alterações pessoais de identidade em commits por acidente.

## Executar o exemplo atual

Na raiz do projeto:

```sh
uv run --locked python -m src.network.rendezvous.teste
```

Com Make, o equivalente é `make run`.

A execução faz operações reais no servidor. Em caso de sucesso, aparecem a
confirmação de registro, os peers encontrados e `Pressione Enter para sair...`.
Pressione **Enter** para parar a renovação e solicitar UNREGISTER. Não use a
execução direta do arquivo (`python src/network/rendezvous/teste.py`): execute
como módulo com `-m`, conforme acima, para resolver os imports corretamente.

O carregador localiza `config.json` pela pasta do projeto, mas os comandos
`uv` e os imports do exemplo devem ser executados na raiz.

## Desenvolvimento e qualidade

Após clonar, cada integrante deve instalar o hook uma vez:

```sh
uv run --locked pre-commit install
```

O hook requer um clone Git; em uma pasta extraída de ZIP, rode as verificações
manualmente. Todos podem usar o mesmo fluxo sem Make:

```sh
uv run --locked ruff check --fix .
uv run --locked ruff format .
uv run --locked python scripts/check.py
```

- **Ruff:** lint, organização de imports e formatação, com quatro espaços e
  largura configurada de 100 colunas. Revise o diff das correções automáticas.
- **mypy estrito:** verifica `src` e `scripts`; anote parâmetros e retornos.
  Use tipos explícitos e evite esconder erros com `Any` ou `type: ignore`.
- **Testes:** `unittest`, locais, sem chamar o Rendezvous público.
- **EditorConfig:** UTF-8, finais de linha LF e espaços, em editores compatíveis.
- **CI:** workflow configurado para Linux, macOS e Windows em pushes/PRs;
  os resultados só podem ser confirmados após a execução no GitHub.

Os casts existentes na fronteira JSON são anotações estáticas, não validação dos
dados recebidos. A validação integral do protocolo continua pendente.
Para código novo use nomes `snake_case`; interfaces antigas foram preservadas.

### Comandos Make

Execute `make` ou `make help` para listar os atalhos. No Windows, use WSL com
GNU Make instalado, ou os comandos `uv` acima no PowerShell.

| Comando | Uso |
| --- | --- |
| `make setup` | Sincronizar dependências e instalar hook de commit |
| `make install` | Sincronizar `.venv` com `uv.lock` |
| `make hooks` | Instalar o hook neste clone |
| `make check` | Executar lint, verificação de formato, tipos e testes |
| `make lint` | Verificar lint sem alterar arquivos |
| `make format` | Formatar o código |
| `make format-check` | Verificar formato sem alterar arquivos |
| `make fix` | Corrigir lint automaticamente e formatar |
| `make typecheck` | Executar mypy |
| `make test` | Executar os testes locais |
| `make run` | Executar o exemplo Rendezvous; acessa a rede real |
| `make docker-build` | Construir imagem Linux e verificar código durante o build |
| `make docker-check` | Construir imagem e executar as verificações no container |

### Atualizar dependências

Após atualizar a branch, execute `uv sync --locked` (ou `make install`).
Para adicionar bibliotecas, use `uv add nome`; para ferramentas, `uv add --dev nome`.
Versione `pyproject.toml`, `.python-version` e `uv.lock`. Não versione `.venv`.
Se `--locked` acusar divergência, confira se recebeu os três arquivos corretos;
quem alterou as dependências deve atualizar e versionar o lockfile.

O hook local pode ser ignorado. Para impedir merge com verificações falhando,
o administrador precisa configurar os checks obrigatórios na proteção da branch.

## Docker e Dev Container

`.venv` isola bibliotecas Python, não o sistema operacional. A imagem Docker
fornece um ambiente Linux. Instale e inicie Docker Desktop (macOS/Windows) ou
Docker Engine (Linux); `docker info` deve conseguir acessar o serviço.

Na raiz do projeto:

```sh
docker build -t pyp2p-forca .
docker run --rm pyp2p-forca uv run --locked python scripts/check.py
```

Para executar o **exemplo Rendezvous** dentro da imagem:

```sh
docker run --rm -it pyp2p-forca uv run --locked python -m src.network.rendezvous.teste
```

Edite `config.json` **antes do build**, pois ele é copiado para a imagem. Reconstrua
a imagem após mudar a configuração ou o código. `-it` permite responder ao prompt
com Enter. O comando `docker run pyp2p-forca` sozinho chama `src.main`, que ainda
está vazio, e termina sem executar o exemplo.

A imagem não instala Git nem Make; use os comandos `uv` dentro dela. No VS Code,
com a extensão Dev Containers e Docker ativo, use **Dev Containers: Reopen in
Container**. O ambiente Python fica em `/opt/forca-venv`, separado da `.venv` do host.
O `postCreateCommand` tenta instalar o hook, que depende de Git disponível no
container; se essa etapa falhar, instale o hook no host e use as verificações
manuais no container. A abertura do Dev Container não foi validada nesta revisão.

A imagem fixa versões de Python e uv e instala o lockfile. Tags das imagens ainda
podem mudar no registro. Para conexões P2P de entrada, quando implementadas, será
preciso publicar a porta (por exemplo `-p 8081:8081`) e escutar em `0.0.0.0` no
container. Hoje o exemplo não abre essa porta. NAT, firewall e redes restritas
podem impedir conexões diretas mesmo com o ambiente instalado corretamente.

## Problemas comuns

| Sintoma | O que conferir |
| --- | --- |
| `uv` não encontrado | Instalação do uv, PATH e reabertura do terminal |
| `make` não encontrado | Use os comandos `uv`, ou instale GNU Make no seu ambiente |
| `No module named src` | Execute na raiz e use `python -m src.network.rendezvous.teste` via uv |
| Erro ao ler `config.json` | Arquivo presente, JSON válido e campos obrigatórios preservados |
| Erro de DNS, timeout ou conexão recusada | Host/porta do Rendezvous, acesso à internet e disponibilidade do servidor |
| Nenhum peer encontrado | Pode não haver outros peers no namespace; o próprio peer é filtrado |
| Python/dependências não baixam | Conectividade, proxy/certificados e suporte do uv à plataforma |
| Docker não conecta ao daemon | Inicie o Docker e confira `docker info` |
| Container termina imediatamente | Passe o comando explícito do exemplo; `src.main` ainda está vazio |
| Hook não instala | Use um clone Git com Git disponível; não uma extração ZIP |

## Validação

Lint, formatação, mypy e quatro testes locais passaram anteriormente no macOS e
no build Linux. Isso valida as verificações e contratos cobertos pelos testes;
não comprova um jogo completo, conectividade pública nem funcionamento em todas
as plataformas. O exemplo pode terminar sem código de erro mesmo quando o
registro falha: confira as mensagens exibidas, não apenas o status do processo.

## Acompanhamento do projeto

- [Issues do projeto](https://github.com/arthurvserodio/Jogo-da-forca_Redes_de_computadores/issues)
