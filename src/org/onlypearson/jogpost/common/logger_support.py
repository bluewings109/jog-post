import logging

# TODO: 비동기 로거 설정, 로거 설정 yaml로 빼기
def get_logger(logger_name: str) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    return logger
