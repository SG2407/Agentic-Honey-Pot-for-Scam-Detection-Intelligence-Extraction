import logging
import sys
from datetime import datetime
from pythonjsonlogger import jsonlogger
from config.settings import settings

def setup_logger(name: str = __name__) -> logging.Logger:
    """Set up structured JSON logging."""
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Create JSON formatter
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

def log_conversation_event(logger: logging.Logger, event_type: str, session_id: str, data: dict = None):
    """Log conversation events with structured data."""
    log_data = {
        'event_type': event_type,
        'session_id': session_id,
        'timestamp': datetime.utcnow().isoformat(),
        'data': data or {}
    }
    logger.info(f"Conversation event: {event_type}", extra=log_data)

def log_scam_detection(logger: logging.Logger, session_id: str, is_scam: bool, confidence: float, scam_type: str = None):
    """Log scam detection results."""
    log_data = {
        'event_type': 'scam_detection',
        'session_id': session_id,
        'is_scam': is_scam,
        'confidence': confidence,
        'scam_type': scam_type,
        'timestamp': datetime.utcnow().isoformat()
    }
    logger.info("Scam detection completed", extra=log_data)

def log_intelligence_extraction(logger: logging.Logger, session_id: str, intelligence: dict):
    """Log intelligence extraction results."""
    log_data = {
        'event_type': 'intelligence_extraction',
        'session_id': session_id,
        'intelligence': intelligence,
        'timestamp': datetime.utcnow().isoformat()
    }
    logger.info("Intelligence extracted", extra=log_data)