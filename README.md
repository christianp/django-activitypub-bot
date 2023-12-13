# A Django ActivityPub bot server

This is a [Django](https://www.djangoproject.com/) project for serving ActivityPub actors, designed for bot accounts.

The aim is to provide just enough features to provide an account that other people can follow, and to manage followers and sending out new posts.

I'm sharing this code as-is, only because it doesn't cost me anything other than the time to write this README!

I hope it's useful, and you're very welcome to use it as a starting-point to build your own project.

If you're looking for a more extensible Python ActivityPub implementation, [bovine](https://github.com/HelgeKrueger/bovine) is worth looking at first.

## Installation

Assumptions:

* You have an existing web server serving a site under a domain name that you'd like to use for an ActivityPub actor, with root (superuser) access.
* These instructions are for a server running Ubuntu Linux, with the nginx web server.

You need Python 3.9 or later to run this.

Clone this repository (I cloned it into `/srv/activitypub`, so that's what these instructions will use), and install the requirements, with 

```
pip install -r requirements.txt
```

It's a good idea to set up a [virtual environment](https://docs.python.org/3/library/venv.html) to do this in.
I set up a virtual environment in `/srv/activitypub/venv`.

Make sure you activate the virtual environment after creating it!

Copy `activitypub_bot/settings.py.dist` to `activitypub_bot/settings.py`, and fill in the settings, following the instructions in that file.

Copy the files in `systemd_services` to `/etc/systemd/system`, and enable them:

Copy `gunicorn.conf.py.dist` to `gunicorn.conf.py` and change it if you used different paths for the repository or the virtual environment.

Run `python manage.py migrate` to set up the database.

Enable the services:

```
systemctl enable activitypub_huey.service activitypub.service activitypub.socket
```

For each domain you want to run ActivityPub on, the server needs to handle requests to the URL `/.well-known/webfinger` and anything under `/activitypub`.
(You can replace `/activitypub` with something else if you want).

Add the following rules to each nginx config that handles domains you want to run ActivityPub on:

```
server {
    # ... your existing config

    location ~ /activitypub/static {
        rewrite ^/activitypub/static/(.*)$ /$1 break;
        root /srv/activitypub/public/static;
    }
    location ~ /activitypub {
        include proxy_params;
        proxy_pass http://unix:/run/activitypub.sock;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
    location = /.well-known/webfinger {
        include proxy_params;
        proxy_pass http://unix:/run/activitypub.sock;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
}
```

Reload nginx's config:

```
systemctl reload nginx
```

It's useful to create superuser login details for the admin interface:

```
python manage.py createsuperuser
```

If everything is set up properly, `https://{DOMAIN}/activitypub/admin` will show you the Django admin login screen.

## Usage

You can create an actor on the command-line with the `create_actor` management command:

```
python manage.py create_actor
```

You'll be asked to choose the domain it should exist on, and to give a username. You can optionally create an API access token.

You can write a post through the admin interface: click on *Local actors*, then on the actor you want to create the post, and then click the *Create a note* link at the bottom of the page.

Alternately, if you created an API access token, you can make a POST request to `https://{DOMAIN}/activitypub/account/{USERNAME}/create_note`.
The request should have the header `Authorization: Bearer {ACCESS_TOKEN}`, and a POST parameter `content` with the text of the post.

## Inbox handlers

When an ActivityPub message is received, it's handled by a series of subclasses of `bot.inbox.AbstractInboxHandler`.

For an activity with `Type: "ActivityType"`, the corresponding method `handle_ActivityType(activity)` on each inbox handler will be called.

Django apps can register a new inbox handler class with `bot.inbox.register_inbox_handler(cls, spec)`. 
`should_handle` is either a callable of the form `spec(actor, activity)` which should return a boolean dictating whether the class should handle this activity received by this actor, or it should be a dictionary with keys `username` and `domain` specifying the usernames, domains, or both, whose inboxes this class should handle.
If `should_handle` is not given, then the handler is called for every activity.

There is a built-in inbox handler, `bot.inbox.InboxHandler`, which manages `Follow` and `Like` activities.

You could define an inbox handler which sends you an email whenever a `Mention` activity is received.

## Help with ActivityPub

The specs are good!

The [ActivityPub protocol specification](https://www.w3.org/TR/activitypub/) gives a description of how interactions work.

The [Activity Streams Vocabulary](https://www.w3.org/TR/activitystreams-vocabulary/) 
