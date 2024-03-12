from __future__ import annotations

import logging

def get_logger(name: str, level:str) -> logging.Logger:
    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    return logging.getLogger(name)

