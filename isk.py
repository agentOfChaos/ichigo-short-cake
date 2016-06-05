import logging


from ichigolib import downloader, cliargs


loglevels = {"info": logging.INFO,
             "debug": logging.DEBUG,
             "warning": logging.WARNING,
             "error": logging.ERROR,
             "critical": logging.CRITICAL}


if __name__ == "__main__":
    cliparse = cliargs.parsecli(", ".join(list(loglevels.keys())))
    md = downloader.MangaDownloader(cliparse.base_url, cliparse.output, cliparse.force, cliparse.update,
                                    cliparse.ignore_incomplete, loglevel=loglevels[cliparse.log_level])
    md.runDownload()