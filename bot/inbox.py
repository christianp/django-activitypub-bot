from   . import activitystreams
from   . import tasks
from   .absolute_url import absolute_reverse
from   django.conf import settings
import json
import uuid

class InboxException(Exception):
    pass

class AbstractInboxHandler:
    def __init__(self, actor):
        self.actor = actor

    def handle(self, activity):
        activity_type = activity.get('type')
        if activity_type is None:
            raise InboxException('This request is missing the type field')

        try:
            handler = getattr(self,'handle_'+activity_type)
        except AttributeError:
            raise InboxException(f'Unrecognised activity type: {activity_type}')

        response = handler(activity)

        if response is None:
            response = {}

        return response

    def handle_Create(self, activity):
        """
            Generic method to handle mentions when a Create activity is received.
        """
        print("Create activity")
        obj = activity.get('object',{})
        if obj.get('type') != 'Note':
            return
        
        mentions_me = any(t for t in obj.get('tag',[]) if t.get('type') == 'Mention' and t.get('href') == self.actor.get_absolute_url())
        if mentions_me:
            self.handle_mention(activity)

    def handle_mention(self, activity):
        """
            :param: activity - JSON for a Create activity.
        """

        tasks.save_mention(self.actor, activity)

class InboxHandler(AbstractInboxHandler):
    """
        An inbox handler for common activitypub tasks: accept follows and unfollows, likes and unlikes.
    """

    def handle_Follow(self, activity):
        try:
            follower = activity['actor']
        except KeyError:
            raise Exception('This request is missing the actor field')

        tasks.add_follower(self.actor, follower, self.accept_message(activity))

        return {'ok': True}

    def handle_Undo(self, activity):
        undone = activity['object']
        activity_type = undone['type']
        try:
            handler = getattr(self,'handle_undo_'+activity_type)
        except AttributeError:
            raise InboxException(f'Unrecognised activity type: {activity_type}')

        return handler(activity)

    def handle_undo_Follow(self, activity):
        follower = activity['actor']
        tasks.remove_follower(self.actor, follower)

        return {'ok': True}

    def handle_Like(self, activity):
        tasks.add_like(self.actor, activity)

    def handle_undo_Like(self, activity):
        tasks.remove_like(self.actor, activity)

    @activitystreams.with_context([activitystreams.ACTIVITYSTREAMS_CONTEXT, activitystreams.SECURITY_CONTEXT])
    def accept_message(self, activity):
        return activitystreams.add_unique_id(self.actor.domain, {
            'type': 'Accept',
            'actor': self.actor.get_absolute_url(),
            'object': activity,
        })

inbox_handlers = [
    (InboxHandler, {}),
]

def register_inbox_handler(handler_cls, spec = None):
    """
        Register an inbox handler class.

        :param: spec - A dict with any of the keys 'username' or 'domain', specifying which actors this class should be used for, or a callable given parameters 'actor' and 'activity'.
    """
    inbox_handlers.append((handler_cls, spec))

def get_inbox_handlers(actor, activity):
    """
        A generator which yields all registered inbox handler classes which should handle the given activity for the given actor.
    """

    for handler_cls, spec in inbox_handlers:
        if spec is None:
            use = True
        elif callable(spec):
            use = spec(actor, activity)
        else:
            use = spec.get('username', actor.username) == actor.username and spec.get('domain', actor.domain) == actor.domain

        if use:
            yield handler_cls(actor)
