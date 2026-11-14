from pathlib import Path

from pydantic import ValidationError

from src.config.loader import ConfigLoader


def main() -> None:
    # Carregar as configurações
    project_root = Path(__file__).parent.parent
    file_path = project_root / "config.json"

    try:
        settings = ConfigLoader(file_path).load()
        print(settings.model_dump_json(indent=2))

    # Validar as configurações
    except ValidationError as error:
        # TODO: Passar os erros para o sistema de logs
        print("Configuração inválida")
        for detail in error.errors():
            field = ".".join(str(part) for part in detail["loc"])
            print(f"- {field or 'arquivo de configurações'}: {detail['msg']}")

    except (OSError, UnicodeError) as error:
        print("Não foi possível ler arquivo de configurações: ", error)

    # Criar Peer Local

    # Criar PeerTable (banco de dados)

    # Criar o ConnectionManager

    # Registra no Rendezvous

    # Descobre os Peers e faz conexão

    # Comandos da CLI

    # Rotina de fechamento


if __name__ == "__main__":
    main()
