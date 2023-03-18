from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from bot.views import testview, webfinger

urlpatterns = [
    path('', testview, name='test'),
    path('account/', include('bot.urls')),
    path('admin/', admin.site.urls),
]

urlpatterns += [path(f'{appname}/', include(f'{appname}.urls', namespace=appname)) for appname in settings.ACTIVITYPUB_APPS]

URL_PREFIX = getattr(settings,'URL_PREFIX','')
if URL_PREFIX != '':
    urlpatterns = [path(URL_PREFIX, include(urlpatterns)),]

urlpatterns += [
    path('.well-known/webfinger', webfinger),
]
