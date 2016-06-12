import requests

useragent = "Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0"

req_cache = {}  # cache requests for performance

def cachedGet(url, params, force_redo=False):
    """
    perform a get request. Successful requests are cached to reduce bandwidth
    """
    ident = (url, params)
    if ident in req_cache.keys() and not force_redo:
        return req_cache[ident]
    req = requests.get(
        url,
        params=params,
        headers = {
            "User-Agent": useragent
        })
    if req.status_code == 200:  # cache only successful requests
        req_cache[ident] = req
    return req

def uncachedHead(url, params):
    """
    head request, non cached
    """
    req = requests.head(
        url,
        params=params,
        headers = {
            "User-Agent": useragent
        })
    return req

def paranoidGet(url, params, timeout=30):
    """
    get request, non cached
    """
    req = requests.get(
        url,
        params=params,
        headers = {
            "User-Agent": useragent
        },
        timeout=timeout
    )
    return req