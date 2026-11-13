import logging
import sys

def setup_logger(log_file=None, level=logging.INFO):
    # Formato exigido: [Timestamp] [Módulo] Nível - Mensagem
    formatter = logging.Formatter('[%(asctime)s] [%(name)s] %(levelname)s - %(message)s', datefmt='%H:%M:%S')
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Log na tela (CLI e mensagens INFO/WARNING)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Log completo em arquivo (incluindo JSON bruto em DEBUG)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG) 
        root_logger.addHandler(file_handler)

    return root_logger