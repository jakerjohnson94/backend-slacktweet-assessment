import logging


def create_logger(name):
    """
    Settup a logger with a stream handler and format for our bot logging
    """
    # create formatter
    FORMAT = '%(asctime)s.%(msecs)03d  %(name)s  %(levelname)s: %(message)s'
    # create logger
    logging.basicConfig(format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    return logger
