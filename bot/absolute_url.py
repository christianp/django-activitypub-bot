from   django.conf import settings
from   django.urls import reverse, resolve
from   urllib.parse import urlparse

def absolute_reverse(name, domain, *args, **kwargs):
    url = reverse(name, args=args, kwargs=kwargs)
    scheme = settings.SCHEME
    return f'{scheme}://{domain}{url}'

def absolute_resolve(url):
    path = urlparse(url).path
    return resolve(path)
