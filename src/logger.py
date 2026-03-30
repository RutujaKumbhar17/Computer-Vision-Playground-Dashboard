import logging
import os
from datetime import datetime

def setup_logger():
    """Sets up the global system logger."""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, 'system.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('CV_Playground')

logger = setup_logger()

def log_algorithm(name, params, execution_time, status="SUCCESS", error=None):
    """Logs details about an algorithm's execution."""
    msg = f"Algorithm: {name} | Params: {params} | Time: {execution_time:.4f}s | Status: {status}"
    if error:
        msg += f" | Error: {error}"
    logger.info(msg)
