from   .absolute_url import absolute_reverse
from   .inbox import InboxException, get_inbox_handlers
from   .models import LocalActor, RemoteActor, Note
from   django.conf import settings
from   django.core.exceptions import PermissionDenied
from   django.core.paginator import Paginator
from   django.views.decorators.csrf import csrf_exempt
from   django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from   django.shortcuts import render, redirect
from   django.utils.decorators import method_decorator
from   django.views import View
import json
import re

# Create your views here.

def testview(request):
    accounts = LocalActor.objects.filter(domain=request.get_host())
    return render(request, 'index.html', {'accounts': accounts})

def guidview(request):
    return HttpResponse('OK?')

def webfinger(request):
    resource = request.GET.get('resource')
    m = re.match(r'^acct:(?P<username>.+?)@(?P<domain>.+)$', resource)
    username = m.group('username')
    domain = m.group('domain')
    with open('/tmp/poo', 'w') as f:
        f.write(f'{username}@{domain}')
    try:
        actor = LocalActor.objects.get(username = username, domain = domain)
    except LocalActor.DoesNotExist:
        return HttpResponseNotFound('')
    data = {
        "subject": f"acct:{actor.username}@{actor.domain}",
        "links": [
            {
                "rel": "self",
                "type": "application/activity+json",
                "href": actor.get_absolute_url(),
            }
        ]
    }
    return JsonResponse(data, content_type='application/jrd+json')

class CSRFExemptMixin:
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args,**kwargs)

class RequireTokenMixin:
    """
        Request must include a token in the Authorization header, or a POST or GET parameter.
    """

    def get_given_token(self):
        """
            Get the token from the request.
        """
        authorization_header = self.request.headers.get('Authorization')
        if authorization_header:
            m = re.match('Bearer (?P<token>.*)', authorization_header)
            if m:
                return m.group('token')

        return self.request.POST.get('token', self.request.GET.get('token'))

    def validate_token(self, given_token):
        """
            Validate the given token: raise a PermissionDenied exception if it is not valid.
        """
        if not self.get_actor().access_tokens.filter(access_token = given_token).exists():
            header = self.request.headers.keys()
            raise PermissionDenied(f"{given_token} is invalid {header}")


    def dispatch(self, request, *args, **kwargs):
        self.validate_token(self.get_given_token())

        return super().dispatch(request, *args, **kwargs)

class ActorView(View):
    def get_actor(self):
        username = self.kwargs['username']
        return LocalActor.objects.get(username = username, domain = self.request.get_host())

class ProfileView(ActorView):
    def get_template_names(self):
        actor = self.get_actor()

        return [
            f'by_domain/{actor.domain}/by_user/{actor.username}/profile.html',
            f'by_domain/{actor.domain}/profile.html',
            'profile.html',
        ]

    def get(self, request, *args, **kwargs):
        actor = self.get_actor()

        paginator = Paginator(actor.notes.all(), 5)

        page_number = request.GET.get('page')
        page = paginator.get_page(page_number)

        if self.request.accepts('text/html'):
            return render(self.request, self.get_template_names(), {'actor': actor, 'profile': actor.actor_json(), 'page': page,})
        else:
            return JsonResponse(actor.actor_json())

class UpdateProfileView(ActorView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        from . import tasks

        actor = self.get_actor()
        tasks.update_profile(actor)
        
        return redirect(actor.get_absolute_url())

class FollowersView(ActorView):
    def get(self, request, *args, **kwargs):
        actor = self.get_actor()
        json = actor.followers_json()
        return JsonResponse(json)

class InboxView(CSRFExemptMixin, ActorView):
    def post(self, request, *args, **kwargs):
        activity = json.load(request)

        actor = self.get_actor()
        inbox_handlers = get_inbox_handlers(actor, activity)

        result = None

        for inbox_handler in inbox_handlers:
            try:
                print(inbox_handler,"handling")
                hresult = inbox_handler.handle(activity)
                print("Activity result:",result)
                if hresult is not None:
                    result = hresult

            except InboxException as e:
                print("Inbox error: ",e)

        if result is not None:
            return JsonResponse(result)
        else:
            return HttpResponse('')

class OutboxView(ActorView):
    def get(self, request, *args, **kwargs):
        actor = self.get_actor()
        json = actor.outbox_json()
        return JsonResponse(json)

class NoteView(ActorView):
    def get_note(self):
        uid = self.kwargs['uid']
        return self.get_actor().notes.get(uid = uid)

    def get(self, request, *args, **kwargs):
        note = self.get_note()

        if self.kwargs.get('content-type') == 'json' or not self.request.accepts('text/html'):
            return JsonResponse(note.note_json())
        else:
            return render(self.request, 'note.html', {'note': note})

class CreateNoteView(CSRFExemptMixin, RequireTokenMixin, ActorView):
    def post(self, request, *args, **kwargs):
        content = request.POST['content']
        note = self.get_actor().create_note(content)
        return redirect(note.get_absolute_url())
