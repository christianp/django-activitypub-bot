from   bot.models import LocalActor, AccessToken
from   django.conf import settings
from   django.core.management.base import BaseCommand, CommandError
import json
import uuid

class Command(BaseCommand):
    help = 'Extract unit tests from one or more questions'

    def handle(self, *args, **options):
        self.options = options

        print("Creating a new local actor.")

        for i, domain in enumerate(settings.DOMAINS):
            print(f'{i}\t{domain}')
        
        rdomain = input("Which domain? ")
        domain = settings.DOMAINS[int(rdomain)]
        username = input("Username: ")

        print(f"The actor will be @{username}@{domain}")

        a = LocalActor.objects.create(username = username, domain = domain)
        a.fill_in_bits()

        if input("Create an API access token? ").lower().strip() == 'y':
            token = str(uuid.uuid4())
            AccessToken.objects.create(actor = a, access_token = token, name = 'Default access token')
            print(f"The API access token is\n    {token}")


        print(f"""The actor has been created. 
You can edit its JSON description at {a.actor_json_file.path}
Its profile page is at {a.get_absolute_url()}
""")


