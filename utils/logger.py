import logging
import sys
from pathlib import Path
from config.settings import LOG_DIR


def setup_logger(name: str, level=logging.INFO, to_file: bool = True):
    """Set up a logger with stream and optional file handlers."""
    logger = logging.getLogger(name)
    if logger.handlers:
        # Logger is already configured
        return logger
    
    logger.setLevel(level)
    
    # Formatter
    fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    # Stream Handler (console)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    
    # File Handler (optional)
    if to_file:
        log_dir = Path(LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_dir / f'{name}.log', mode='a', encoding='utf-8')
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        
    return logger
