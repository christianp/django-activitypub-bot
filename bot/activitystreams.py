import email.utils
from   datetime import datetime
from   functools import wraps
import itertools
from   math import ceil
import uuid
from   .absolute_url import absolute_reverse

PUBLIC = "https://www.w3.org/ns/activitystreams#Public"
ACTIVITYSTREAMS_CONTEXT = "https://www.w3.org/ns/activitystreams"
SECURITY_CONTEXT = "https://w3id.org/security/v1"

def format_datetime(time):
    return time.strftime('%Y-%m-%dT%H:%M:%SZ')

def now():
    return format_datetime(datetime.now())

def unique_message_url(domain):
    return absolute_reverse('guid', domain=domain, guid=str(uuid.uuid4()))

def add_context(message, context=[ACTIVITYSTREAMS_CONTEXT]):
    message.update({
        '@context': context
    })
    return message

def with_context(context=[ACTIVITYSTREAMS_CONTEXT]):
    def inner(fn):
        @wraps(fn)
        def wrapper(*args,**kwargs):
            message = fn(*args, **kwargs)
            message = add_context(message, context)
            return message

        return wrapper

    return inner

def add_unique_id(domain, message):
    message['id'] = unique_message_url(domain)
    return message

def ordered_collection(per_page=20):
    def inner(fn):
        @wraps(fn)
        @with_context()
        def wrapper(*args, page=0, **kwargs):
            all_items, num_items, uid = fn(*args, **kwargs)
            num_pages = ceil(num_items/per_page)
            page_items = list(itertools.islice(all_items, page*per_page, (page+1)*per_page))
            page_key = 'first' if page==0 else 'last' if page >= num_pages-1 else 'current'
            return {
                "type": "OrderedCollection",
                "totalItems": num_items,
                "id": uid,
                page_key: {
                    "type": "OrderedCollectionPage",
                    "totalItems": min(per_page, num_items - per_page*page),
                    "partOf": uid,
                    "orderedItems": page_items, 
                    "id": f"{uid}?page={page}"
                },
            }

        return wrapper

    return inner
