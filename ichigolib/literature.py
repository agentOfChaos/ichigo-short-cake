

class Manga:

    def __init__(self, mangatitle, baseurl):
        self.mangatitle = mangatitle
        self.baseurl = baseurl
        self.chapters = []

    @property
    def completed(self):
        if len(self.chapters) == 0:
            return False
        for chapter in self.chapters:
            if not chapter.completed:
                return False
        return True

    @property
    def already_dl_chapters(self):
        if len(self.chapters) == 0:
            return False
        for chapter in self.chapters:
            if not chapter.already_dl:
                return False
        return True

    def getIncompleteChapters(self):
        ret = []
        for chapter in self.chapters:
            if not chapter.completed:
                ret.append(chapter)
        return ret


class Chapter:

    def __init__(self, mangatitle, chaptertitle, baseurl, id, already_dl=False):
        self.mangatitle = mangatitle
        self.chaptertitle = chaptertitle
        self.baseurl = baseurl
        self.id = id
        self.pages = []
        self.already_dl = already_dl

    @property
    def completed(self):
        if len(self.pages) == 0:
            return False
        for page in self.pages:
            if not page.completed:
                return False
        return True

    def getIncompletePages(self):
        ret = []
        for page in self.pages:
            if not page.completed:
                ret.append(page)
        return ret

    def getSaveName(self):
        return "[%d] - %s" % (self.id, self.chaptertitle)


class Page:

    def __init__(self, id, baseurl, picurl):
        self.id = id
        self.baseurl = baseurl
        self.picurl = picurl
        self.visited = False
        self.downloaded = False

    @property
    def completed(self):
        return self.downloaded
