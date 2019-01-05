import logging


def create_logger():
    """
    Settup logger level and format
    """
    # create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter
    formatter = logging.Formatter(
        '\n%(asctime)s  %(levelname)s:\n%(message)s',
        datefmt='%Y-%m-%d  %H:%M:%S')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)
    return logger
