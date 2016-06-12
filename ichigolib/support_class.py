import logging, sys

"""
Utility code
"""

class LogMaster:
    def setLogger(self, name, loglevel):
        self.loglevel = loglevel
        self.logger = logging.getLogger(name)
        self.logger.setLevel(loglevel)
        self.logger.handlers = []
        ch = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s: [%(name)s][%(levelname)s]: %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    @staticmethod
    def setStaticLogger(owner, name, loglevel):
        owner.loglevel = loglevel
        owner.logger = logging.getLogger(name)
        owner.logger.setLevel(loglevel)
        owner.logger.handlers = []
        ch = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s: [%(name)s][%(levelname)s]: %(message)s')
        ch.setFormatter(formatter)
        owner.logger.addHandler(ch)