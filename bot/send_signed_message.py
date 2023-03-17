# from https://github.com/HelgeKrueger/bovine/blob/975855232b74dca2a6f55358a9f3f5647e9c0717/bovine/clients/signed_http.py

import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import (load_pem_private_key,load_pem_public_key)
from datetime import datetime, timedelta, timezone
from dateutil.parser import parse
import hashlib
import requests
from   urllib.parse import urlparse

def get_gmt_now() -> str:
    return datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

def sign_message(private_key, message):
    key = load_pem_private_key(private_key, password=None)

    return base64.standard_b64encode(
        key.sign(
            message.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    ).decode("utf-8")

class HttpSignature:
    def __init__(self):
        self.fields = []

    def build_signature(self, key_id, private_key):
        message = self.build_message()

        signature_string = sign_message(private_key, message)
        headers = " ".join(name for name, _ in self.fields)

        signature_parts = [
            f'keyId="{key_id}"',
            'algorithm="rsa-sha256"',  # FIXME: Should other algorithms be supported?
            f'headers="{headers}"',
            f'signature="{signature_string}"',
        ]

        return ",".join(signature_parts)

    def verify(self, public_key, signature):
        message = self.build_message()
        return verify_signature(public_key, message, signature)

    def build_message(self):
        return "\n".join(f"{name}: {value}" for name, value in self.fields)

    def with_field(self, field_name, field_value):
        self.fields.append((field_name, field_value))
        return self

def content_digest_sha256(content):
    if isinstance(content, str):
        content = content.encode("utf-8")

    digest = base64.standard_b64encode(hashlib.sha256(content).digest()).decode("utf-8")
    return "SHA-256=" + digest


def build_signature(host, method, target):
    return (
        HttpSignature()
        .with_field("(request-target)", f"{method} {target}")
        .with_field("host", host)
    )
def signed_post(url, private_key, public_key_url, headers = None, body = None):
    headers = {} if headers is None else headers

    parsed_url = urlparse(url)
    host = parsed_url.netloc
    target = parsed_url.path

    accept = "application/activity+json"
    content_type = "application/activity+json"
    date_header = get_gmt_now()

    digest = content_digest_sha256(body)

    signature_header = (
        build_signature(host, "post", target)
        .with_field("date", date_header)
        .with_field("digest", digest)
        .with_field("content-type", content_type)
        .build_signature(public_key_url, private_key)
    )

    headers["accept"] = accept
    headers["digest"] = digest
    headers["date"] = date_header
    headers["host"] = host
    headers["content-type"] = content_type
    headers["signature"] = signature_header
    headers["user-agent"] = "CLPs activitypub bot"

    response = requests.post(url, data = body, headers = headers)
    print(f"Sent to {url}!")
    print(response)
    return response
