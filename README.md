# Description

Ichigo Short Cake is a command line, multi-threaded, fault-tolerant manga downloader

# Abstract

Basically one day I was trying to read manga online. Emphasis on "try", because the site
took forever to load the next page; it was just a temporary issue, yet still...  
Then, I tried a couple of downloader programs I could find in the repos, but either:

1. I could not figure out how to make it work
2. Some pages would come out "damaged"

So I moved on to code my own manga downloader, to be able to download from such an "unreliable"
server, and I made it simple to use, too ("simple" if you are a cli-oriented person :)


# Running

## Example:

    python isk.py http://www.mangahere.co/manga/hatsune_mix/
    
By default, the manga will be downloaded inside a sub-folder of ~/manga

# Help

To get a list of supported sites, plus help on the various cli parameters, run

    python isk.py --help
    
# Hacking

If you want to personally add support for new manga sites, just implement the interface BaseScanner  
Also, update the ScannerFactory.loadScanners to also initialize your own scanner