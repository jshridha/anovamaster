#!/usr/bin/env python

import logging
import logging.handlers

from AnovaMaster import AnovaConfiguration, AnovaMaster

def main():
    config = AnovaConfiguration()
    log_setup(config.get('main', 'log_file'),
              config.get('main', 'log_level'))
    logging.info('AnovaMaster starting...')
    logging.info('Setting up connection')
    my_anova = AnovaMaster(config)
    logging.info('Running main loop')
    my_anova.run()

def log_setup(filename, log_level):
    log_handler = logging.handlers.WatchedFileHandler(filename)
    formatter = logging.Formatter(
        '%(asctime)s %(message)s',
        '%b %d %H:%M:%S')
    log_handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(log_handler)
    logger.setLevel(log_level)

if __name__ == '__main__':
    main()
