import json
from   pathlib import Path
import requests

WEBFINGER_TIMEOUT = 10

remote_accounts_dir = Path('remote-accounts')

class WebfingerException(Exception):
    def __init__(self, error):
        super().__init__()
        self.error = error

def webfinger(username, domain):
    try:
        res = requests.get(
            f'https://{domain}/.well-known/webfinger',
            params = {
                'resource': f'acct:{username}@{domain}',
            },
            headers = {
                'Accept': 'application/jrd+json',
            },
            timeout = WEBFINGER_TIMEOUT,
            verify = True
        )
        webfinger_data = res.json()
    except requests.RequestException as e:
        data = None
        return

    profile_link = next((rel for rel in webfinger_data.get('links',[]) if rel.get('rel') == 'self' and rel.get('type') == 'application/activity+json'), None)
    if profile_link is not None:
        profile_data = fetch_remote_profile(profile_link.get('href'))
    else:
        profile_data = None

    data = {
        'webfinger': webfinger_data,
        'profile': profile_data,
    }

    return data

def fetch_remote_profile(url):
    res = requests.get(
        url,
        headers = {
            'Accept': 'application/json',
        }
    )
    profile_data = res.json()

    return profile_data
