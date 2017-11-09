import logging
import re
from bs4 import BeautifulSoup


from ichigolib.scanners.basescanner import BaseScanner
from ichigolib.requester import cachedGet
from ichigolib.literature import Chapter


class MangaReaderScanner(BaseScanner):

    urlmatcher = re.compile("http:\/\/www\.mangareader\.net\/([^\/]+)\/")

    def __init__(self, loglevel=logging.INFO):
        super().__init__(loglevel)

    def doesApply(self, baseurl):
        return self.urlmatcher.match(baseurl) is not None

    def getTitle(self, baseurl):
        pagehtml = cachedGet(baseurl, None).text
        soup = BeautifulSoup(pagehtml, "html.parser")
        try:
            mangaproperties = list(soup.find_all("div", attrs={"id": "mangaproperties"}))[0]
            title = list(mangaproperties.find_all("h2", attrs={"class": "aname"}))[0].get_text()
            return title
        except Exception:
            return baseurl

    def getChapterList(self, manga):
        chapters = []
        pagehtml = cachedGet(manga.baseurl, None).text
        soup = BeautifulSoup(pagehtml, "html.parser")
        listing = list(soup.find_all("table", attrs={"id": "listing"}))[0]
        rows = listing.find_all("tr")
        id = 0
        for tr in rows:
            id += 1
            a_tag = tr.find("a")
            if a_tag is not None:
                chapters.append(Chapter(manga.title, a_tag.get_text(), manga.baseurl + a_tag["href"], id))
        return chapters

    def getNextPage(self, currentpageurl):
        pagehtml = cachedGet(currentpageurl, None).text
        soup = BeautifulSoup(pagehtml, "html.parser")
        viewer = list(soup.find_all("id", attrs={"id": "imgholder"}))[0]
        a = list(viewer.find_all("a"))[0]
        return a["href"]

    def getImageUrl(self, currentpageurl):
        pagehtml = cachedGet(currentpageurl, None).text
        soup = BeautifulSoup(pagehtml, "html.parser")
        a = list(soup.find_all("img", attrs={"id": "img"}))[0]
        return a["src"]

    def hasNextPage(self, currentpageurl):
        return self.getNextPage(currentpageurl).startswith("http")