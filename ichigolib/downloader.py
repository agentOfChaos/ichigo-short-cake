import logging
import os
import imghdr
from slugify import slugify
import time
import re
import requests


from ichigolib.support_class import LogMaster
from ichigolib.scanners import scannerfactory
from ichigolib.job_manager import JobManager, Job
from ichigolib.literature import Manga, Page
from ichigolib.requester import uncachedHead, paranoidGet
from ichigolib.faultcounter import FaultCounter


class SpiderJob(Job):

    def __init__(self, chapter, pageurl, pageid, scanner, jobmanager, savelocation,
                 loglevel=logging.INFO, tolerance=20, ignore_incomplete=False, force=False):
        super().__init__(loglevel=loglevel)
        self.chapter = chapter
        self.pageurl = pageurl
        self.pageid = pageid
        self.scanner = scanner
        self.jobmanager = jobmanager
        self.savelocation = savelocation
        self.ignore_incomplete = ignore_incomplete
        self.force = force
        self.tolerance = tolerance
        self.tolerated = 0

    def faultToll(self):
        self.tolerated += 1
        if self.tolerated < self.tolerance:
            self.logger.warning("Restarting scan of %s" % self.pageid)
            return True
        else:
            self.logger.error("Fault tolerance exceeded! (page %s)" % self.pageid)
            FaultCounter.spider_faults += 1
            return False

    def payload(self):
        """
        use the scanner to extract useful data from a page, then schedules a job to download the page's embedded image,
        and another job to crawl the next page (if any)
        """
        self.logger.debug("Acquiring %s#%d..." % (self.chapter.chaptertitle, self.pageid))
        pagepic = self.scanner.getImageUrl(self.pageurl)
        pageobj = Page(self.pageid, self.pageurl, pagepic)
        self.chapter.pages.insert(self.pageid, pageobj)
        self.jobmanager.putjob(PicDloadJob(pageobj, self.savelocation, loglevel=self.loglevel, force=self.force,
                                           ignore_incomplete=self.ignore_incomplete))
        self.logger.debug("Acquired %s#%d" % (self.chapter.chaptertitle, self.pageid))
        if self.scanner.hasNextPage(self.pageurl):
            nextpage = self.scanner.getNextPage(self.pageurl)
            self.jobmanager.putjob(SpiderJob(self.chapter, nextpage, self.pageid+1, self.scanner, self.jobmanager,
                                             self.savelocation, loglevel=self.loglevel,
                                             ignore_incomplete=self.ignore_incomplete))
        pageobj.visited = True

    def execute(self):
        while True:
            try:
                self.payload()
                return
            except Exception as e:
                self.logger.warning("While scanning %s#%d, an exception was caught: \"%s\": %s" %
                                  (self.chapter.chaptertitle, self.pageid, e.__class__.__name__, e))
                if not self.faultToll():
                    return


class PicDloadJob(Job):

    def __init__(self, page, savelocation, loglevel=logging.INFO, tolerance=20, ignore_incomplete=False, force=False):
        super().__init__(loglevel=loglevel)
        self.page = page
        self.savelocation = savelocation
        self.ignore_incomplete = ignore_incomplete
        self.tolerance = tolerance
        self.tolerated = 0
        self.force = force

    def faultToll(self):
        self.tolerated += 1
        if self.tolerated < self.tolerance:
            self.logger.debug("Restarting download of %s" % self.page.picurl)
            return True
        else:
            self.logger.error("Fault tolerance exceeded! (%s)" % self.page.picurl)
            FaultCounter.image_faults += 1
            return False

    def safeDload(self):
        """
        Queries the server for the image size, and then downloads it.
        If there are errors / the image wasn't fully downloaded, we retry downloading it.
        :return: tuple (image blob, is download complete?, expected image size)
        """
        imgsize = 0
        best_size_sofar = 0
        best_data_sofar = (b"", False, 0)

        while True:
            try:
                imgsize = int(uncachedHead(self.page.picurl, None).headers["Content-Length"])
                break
            except Exception as e:
                self.logger.debug("While fetching size of \"%s\", an exception was caught: \"%s\": %s" %
                                  (self.page.picurl, e.__class__.__name__, e))
                if not self.faultToll():
                    return best_data_sofar

        self.logger.debug("Downloading \"%s\", size: %d bytes" % (self.page.picurl, imgsize))

        while True:
            try:
                dldata = paranoidGet(self.page.picurl, None).content
                if len(dldata) >= imgsize:
                    self.logger.debug("Success downloading \"%s\"" % (self.page.picurl,))
                    return (dldata, True, imgsize)
                else:
                    self.logger.debug("Incomplete download of \"%s\"" % self.page.picurl)
                    if len(dldata) > best_size_sofar:
                        best_size_sofar = len(dldata)
                        best_data_sofar = (dldata, False, imgsize)
                    if not self.faultToll():
                        return best_data_sofar
            except requests.exceptions.Timeout:
                self.logger.debug("Hit timemout downloading \"%s\"" % self.page.picurl)
                if not self.faultToll():
                    return best_data_sofar
            except Exception as e:
                self.logger.debug("While downloading \"%s\", an exception was caught: \"%s\": %s" %
                                  (self.page.picurl, e.__class__.__name__, e))
                if not self.faultToll():
                    return best_data_sofar
        return best_data_sofar

    def exists(self):
        """
        check if a page already exists as a downloaded image. For failed/incomplete images,
        special rules are applied.
        """
        candidates = os.listdir(self.savelocation)
        nmatch = re.compile("([0-9]+)\.(.+)")
        for cand in candidates:
            matched = nmatch.match(cand)
            if matched is not None:
                if int(matched.group(1)) == self.page.id:
                    if matched.group(2) == "None":  # a previous failed download
                        os.remove(os.path.join(self.savelocation, cand))
                        return False
                    elif matched.group(2).startswith("part."): # a previous incomplete download
                        if self.ignore_incomplete:
                            return True
                        else:
                            return False
                    return True
        return False

    def execute(self):
        if self.exists() and not self.force:
            self.logger.debug("Skipping %s = %d, already exists" % (self.page.picurl, self.page.id))
            self.page.downloaded = True
            return

        (imgdata, complete, exptected_size) = self.safeDload()
        self.page.downloaded = True

        if not complete:
            self.logger.info("Incomplete, saving anyways %d/%d bytes" % (len(imgdata), exptected_size))

        ext = imghdr.what(None, h=imgdata)
        if ext is None:
            ext = "None"
        elif not complete:
            ext = "part." + ext

        filename = os.path.join(self.savelocation, "%d.%s" % (self.page.id, ext))
        inc_filename = os.path.join(self.savelocation, "%d.part.%s" % (self.page.id, ext))

        if complete and os.path.isfile(inc_filename):
            self.logger.debug("Deleting leftover incomplete image from a previous run")
            os.remove(inc_filename)

        if not self.force and os.path.isfile(filename) and not complete:
            oldsize = os.path.getsize(filename)
            if len(imgdata) <= oldsize:
                self.logger.info("A better version of %s was already on disk. Discarding downloaded data." %
                                 self.page.picurl)
                return

        with open(filename, "wb") as sf:
            sf.write(imgdata)


class MangaDownloader(LogMaster):

    def __init__(self, baseurl, folder, force=False, update=False, ignore_incomplete=False, loglevel=logging.INFO):
        self.setLogger(self.__class__.__name__, loglevel)
        self.baseurl = baseurl
        self.folder = folder
        self.force = force
        self.update = update
        self.ignore_incomplete = ignore_incomplete
        self.checkFolder()
        self.factory = scannerfactory.ScannerFactory(loglevel=self.loglevel)
        self.jobmanager = JobManager(200, loglevel=self.loglevel)
        self.manga = None

    def checkFolder(self):
        if not os.path.isdir(os.path.expanduser(self.folder)):
            self.logger.critical("Destination folder %s does not exist!" % self.folder)
            exit(-1)

    def dl_report(self):
        miselem = []
        mischap = self.manga.getIncompleteChapters()
        for mc in mischap:
            mispage = mc.getIncompletePages()
            #miselem.append("(" + mc.chaptertitle + ")")
            for p in mispage:
                miselem.append(mc.chaptertitle + "#" + str(p.id))
        self.logger.debug("Missing: %s" % ", ".join(miselem))

    def runDownload(self):
        scanner = self.scanBaseUrl()
        self.prepareDirs()
        self.spiderPages(scanner)
        while True:
            time.sleep(5)
            self.dl_report()
            if self.manga.completed:
                break
            if self.update and self.manga.already_dl_chapters:
                self.logger.info("No new chapters are out")
                break

        self.jobmanager.putjob(None)
        self.logger.info("Finished downloading %s" % self.manga.mangatitle)
        self.finalWords()

    def scanBaseUrl(self):
        (sname, scanner) = self.factory.getScanner(self.baseurl)
        if scanner is None:
            self.logger.error("No scanner implemented for %s" % self.baseurl)
            return
        self.logger.info("Scanner %s selected" % sname)
        title = scanner.getTitle(self.baseurl)
        self.manga = Manga(title, self.baseurl)
        self.logger.info("Found manga \"%s\"" % title)
        chapters = scanner.getChapterList(self.manga)
        self.manga.chapters = chapters
        for chapter in chapters:
            newstring = ""
            chapter.already_dl = True
            if not os.path.isdir(self.getChapterDir(chapter)):
                newstring = " NEW"
                chapter.already_dl = False
            self.logger.info("Found chapter \"%s\"%s" % (chapter.getSaveName(), newstring))
        return scanner
        # TODO: find optionals

    def getChapterDir(self, chapter):
        mangadir = os.path.join(os.path.expanduser(self.folder), slugify(self.manga.mangatitle, separator=" "))
        return os.path.join(mangadir, chapter.getSaveName())

    def prepareDirs(self):
        mangadir = os.path.join(os.path.expanduser(self.folder), slugify(self.manga.mangatitle, separator=" "))
        if not os.path.isdir(mangadir):
            os.makedirs(mangadir)
        for chapter in self.manga.chapters:
            chapterdir = os.path.join(mangadir, chapter.getSaveName())
            if not os.path.isdir(chapterdir):
                os.makedirs(chapterdir)

    def spiderPages(self, scanner):
        for chapter in self.manga.chapters:
            chapterdir = self.getChapterDir(chapter)
            if os.path.isdir(chapterdir) and self.update:
                self.logger.debug("Skipping chapter \"%s\", already downloaded" % chapter.chaptertitle)
                continue
            self.jobmanager.putjob(SpiderJob(chapter, chapter.baseurl, 1, scanner, self.jobmanager, chapterdir,
                                             loglevel=self.loglevel, force=self.force,
                                             ignore_incomplete=self.ignore_incomplete))

    def finalWords(self):
        if FaultCounter.image_faults + FaultCounter.spider_faults > 0:
            self.logger.warning("Despite our best effort, we failed downloading "
                                "%d pages and got %d images incomplete. Try running the program again" %
                                (FaultCounter.spider_faults, FaultCounter.image_faults))