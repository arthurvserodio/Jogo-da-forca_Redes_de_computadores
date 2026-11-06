from enum import Enum

class MaqEstadosJogo(Enum):
    IDLE = "IDLE",
    OPEN = "OPEN",
    RUNNING = "RUNNING",
    FINISHED = "FINISHED",
    