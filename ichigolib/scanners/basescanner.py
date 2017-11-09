import logging


from ichigolib.support_class import LogMaster


class BaseScanner(LogMaster):
    """
    Stateless object, implements manga-specific scraping routines
    """

    def __init__(self, loglevel=logging.INFO):
        self.setLogger(self.__class__.__name__, loglevel)

    def doesApply(self, baseurl):
        """ :return: true whether the scanner is suitable for a particular url """
        return False

    def getTitle(self, baseurl):
        """ :return: the manga title, from the manga's details page """
        return ""

    def getChapterList(self, manga):
        """ :return: the manga chapter list, from the manga's details page """
        return []

    def setPageBaseUrl(self, pagebaseurl):
        """ (optional) sets the base-url, in case the next-page link in the page is relative only """
        pass

    def getNextPage(self, currentpageurl):
        """ :return: the url of the next page, given the url of the current page """
        return ""

    def hasNextPage(self, currentpageurl):
        """ :return: false if the current page is the last page in the chapter """
        return False

    def getImageUrl(self, currentpageurl):
        """ :return: the url of the picture embedded in the current page """
        return ""