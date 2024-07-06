from   . import activitystreams
from   .send_signed_message import signed_post, authorized_fetch
from   django.utils import dateparse
from   huey.contrib.djhuey import task
import json
from pprint import pprint

def task():
    def inner(func):
        def moreinner(*args, **kwargs):
            func(*args, **kwargs)

        return moreinner
    return inner

@task()
def update_profile(actor):
    actor.update_profile()

@task()
def send_message(inbox_url, message, private_key_pem, public_key_url):
    print(f"Sending to {inbox_url}:\n{json.dumps(message,indent=4)}")
    signed_post(inbox_url, private_key_pem, public_key_url, body = json.dumps(message))


@task()
def add_follower(actor, follower_url, accept_message):
    from .models import RemoteActor
    remote_actor = RemoteActor.objects.get_by_url(actor, follower_url)
    actor.followers.add(remote_actor)

    actor.send_signed_message(remote_actor.get_inbox_url(), accept_message)

@task()
def remove_follower(actor, follower_url):
    from .models import RemoteActor
    remote_actor = RemoteActor.objects.get_by_url(actor, follower_url)
    actor.followers.remove(remote_actor)

@task()
def add_like(actor, activity):
    from .models import Note, RemoteActor
    note = Note.objects.get_by_absolute_url(activity['object'])
    remote_actor = RemoteActor.objects.get_by_url(actor, activity['actor'])
    note.likes.add(remote_actor)

@task()
def remove_like(actor, activity):
    from .models import Note, RemoteActor
    note = Note.objects.get_by_absolute_url(activity['object']['object'])
    remote_actor = RemoteActor.objects.get_by_url(actor, activity['actor'])
    note.likes.remove(remote_actor)

@task()
def add_announce(actor, activity):
    from .models import Note, RemoteActor
    note = Note.objects.get_by_absolute_url(activity['object'])
    remote_actor = RemoteActor.objects.get_by_url(actor, activity['actor'])
    note.announces.add(remote_actor)

@task()
def remove_announce(actor, activity):
    from .models import Note, RemoteActor
    note = Note.objects.get_by_absolute_url(activity['object']['object'])
    remote_actor = RemoteActor.objects.get_by_url(actor, activity['actor'])
    note.announces.remove(remote_actor)

@task()
def save_mention(recipient, activity):
    from .models import Note, RemoteActor

    remote_actor_url = activity['actor']
    remote_actor = RemoteActor.objects.get_by_url(recipient, remote_actor_url)
    note_json = activity['object']

    try:
        in_reply_to = Note.objects.get_by_absolute_url(note_json.get('inReplyTo'))
    except Exception:
        in_reply_to = None

    note = Note.objects.create(
        remote_actor = remote_actor,
        data = note_json,
        published_date = dateparse.parse_datetime(note_json.get('published')),
        public = activitystreams.PUBLIC in note_json.get('to',[]),
        in_reply_to = in_reply_to
    )

    note.mentions.add(recipient)
