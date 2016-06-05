import logging


from ichigolib.support_class import LogMaster
from ichigolib.scanners.sitespecific import mangahere


class ScannerFactory(LogMaster):
    """
    Instantiates the manga-scanner suitable for a provided url
    """

    def __init__(self, loglevel=logging.INFO):
        self.setLogger(self.__class__.__name__, loglevel)
        self.scanners = {}
        self.loadScanners()
        self.logger.info("Loaded %d manga site scanners" % len(self.scanners))

    def loadScanners(self):
        self.scanners["mangahere"] = mangahere.MangaHereScanner(loglevel=self.loglevel)

    def getScanner(self, baseurl):
        for name, scanner in self.scanners.items():
            if scanner.doesApply(baseurl):
                return (name, scanner)
        return ("None", None)