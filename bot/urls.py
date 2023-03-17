from django.urls import path
from . import views 

urlpatterns = [
    path('object/<uuid:guid>', 
        views.guidview,
        name='guid'
    ),
    path('<str:username>',
        views.ProfileView.as_view(),
        name='user_profile'
    ),
    path('<str:username>/update-profile',
        views.UpdateProfileView.as_view(),
        name='user_update_profile'
    ),
    path('<str:username>/followers',
        views.FollowersView.as_view(),
        name='user_followers'
    ),
    path('<str:username>/inbox',
        views.InboxView.as_view(),
        name='user_inbox'
    ),
    path('<str:username>/outbox',
        views.OutboxView.as_view(),
        name='user_outbox'
    ),

    path('<str:username>/notes/<str:uid>',
        views.NoteView.as_view(),
        name='note'
    ),
    path('<str:username>/notes/<str:uid>/json',
        views.NoteView.as_view(),
        {'content-type': 'json'},
        name='note_json'
    ),
    path('<str:username>/create_note',
        views.CreateNoteView.as_view(),
        name='note_create'
    ),
]

