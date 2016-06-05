import argparse
from ichigolib.scanners.scannerfactory import ScannerFactory


def parsecli(verbstr):
    parser = argparse.ArgumentParser(description="Manga downloader which (hopefully) doesn't suck. "
            "The program downloads comics from free online manga-viewing websites, and saves them in a local "
            "directory structure. It was developed with emphasis on fault-tolerance, parallelism, and requires "
            "minimum user-interaction. The following online manga viewers are supported: %s" %
            ",".join(list(ScannerFactory().scanners.keys())))
    parser.add_argument('-o', '--output', metavar='dir', help='Directory to download to', default='~/manga', type=str)
    parser.add_argument('-f', '--force', help='Force re-download', action='store_true')
    parser.add_argument('-u', '--update', help='Only download new chapters', action='store_true')
    parser.add_argument('-i', '--ignore-incomplete', help='Do not attempt to re-download incomplete images',
                        action='store_true')
    parser.add_argument('-l', '--log-level', metavar='level', help='Logging verbosity (%s)' % verbstr,
                        type=str, default='info')
    parser.add_argument('base_url', help='Description page of the manga to download', type=str)
    return parser.parse_args()