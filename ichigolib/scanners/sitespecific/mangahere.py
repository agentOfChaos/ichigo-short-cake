import logging
import re
from bs4 import BeautifulSoup


from ichigolib.scanners.basescanner import BaseScanner
from ichigolib.requester import cachedGet
from ichigolib.literature import Chapter


class MangaHereScanner(BaseScanner):

    urlmatcher = re.compile("http:\/\/www\.mangahere\.co\/manga\/([^\/]+)\/")

    def __init__(self, loglevel=logging.INFO):
        super().__init__(loglevel)

    def doesApply(self, baseurl):
        return self.urlmatcher.match(baseurl) is not None

    def getTitle(self, baseurl):
        pagehtml = cachedGet(baseurl, None).text
        soup = BeautifulSoup(pagehtml, "html.parser")
        try:
            mr316 = list(soup.find_all("div", attrs={"class": "mr316"}))[0]
            title = list(mr316.find_all("h1", attrs={"class": "title"}))[0].get_text()
            return title
        except Exception:
            return baseurl

    def extractChapter(self, mtitle, li_elem, id):
        left = li_elem.find("span", attrs={"class": "left"})
        a_tag = left.find("a", attrs={"class": "color_0077"})
        url = a_tag["href"]
        a_tag.extract()
        mr_6 = left.find("span", attrs={"class": "mr6"})
        mr_6.append(" ")
        title = left.get_text().strip().replace("  "," ")
        return Chapter(mtitle, title, url, id)

    def getChapterList(self, manga):
        chapters = []
        pagehtml = cachedGet(manga.baseurl, None).text
        soup = BeautifulSoup(pagehtml, "html.parser")
        manga_detail = list(soup.find_all("div", attrs={"class": "manga_detail"}))[0]
        detail_list = list(manga_detail.find_all("div", attrs={"class": "detail_list"}))[0]
        ul1 = list(detail_list.find_all("ul"))[0]
        id = 0
        for li in reversed(ul1.find_all("li")):
            id += 1
            chapters.append(self.extractChapter(manga.mangatitle, li, id))
        return chapters

    def getNextPage(self, currentpageurl):
        pagehtml = cachedGet(currentpageurl, None).text
        soup = BeautifulSoup(pagehtml, "html.parser")
        viewer = list(soup.find_all("section", attrs={"id": "viewer"}))[0]
        a = list(viewer.find_all("a"))[0]
        return a["href"]

    def getImageUrl(self, currentpageurl):
        pagehtml = cachedGet(currentpageurl, None).text
        soup = BeautifulSoup(pagehtml, "html.parser")
        a = list(soup.find_all("img", attrs={"id": "image"}))[0]
        return a["src"]

    def hasNextPage(self, currentpageurl):
        return self.getNextPage(currentpageurl).startswith("http")