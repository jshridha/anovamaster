#!/usr/bin/env python

import logging

from AnovaMaster import AnovaConfiguration, AnovaMaster

def main():
    logging.basicConfig(filename='anovamaster.log',
                        format='%(asctime)s %(message)s',
                        level=logging.INFO)
    logging.info('Importing config')
    config = AnovaConfiguration()
    logging.info('Setting up connection')
    my_anova = AnovaMaster(config)
    logging.info('Running main loop')
    my_anova.run()

if __name__ == '__main__':
    main()
