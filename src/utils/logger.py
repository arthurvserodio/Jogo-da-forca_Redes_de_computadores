
import logging
from pathlib import Path


def configurar_logs(arquivo: str | Path, nivel_console: str = "INFO") -> None:
    # Arquivo é o local onde os loggers seram salvos
    caminho = Path(arquivo) 
    caminho.parent.mkdir(parents=True, exist_ok=True)
    # Formato do log -> quando aconteceu | nivel | nome | mensagem
    formato = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Remove handlers configurados anteriormente.
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()

    # Terminal: apenas mensagens do nível selecionado.
    console = logging.StreamHandler()
    console.setLevel(getattr(logging, nivel_console.upper()))
    console.setFormatter(formato)

    # Arquivo: registra também as mensagens DEBUG.
    arquivo_handler = logging.FileHandler(caminho, encoding="utf-8")
    arquivo_handler.setLevel(logging.DEBUG)
    arquivo_handler.setFormatter(formato)

    root.addHandler(console)
    root.addHandler(arquivo_handler)
