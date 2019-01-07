import logging


def create_logger(name):
    """
    Settup a logger with a stream handler and format for our bot logging
    """
    # create formatter
    FORMAT = '%(asctime)s.%(msecs)03d %(name)s  %(levelname)s: %(message)s'
    # create logger
    logging.basicConfig(format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # # create console handler and set level to debug
    # ch = logging.StreamHandler()
    # ch.setLevel(logging.INFO)

    # # add formatter to ch
    # ch.setFormatter(formatter)
    # # add ch to logger
    # logger.addHandler(ch)
    return logger
