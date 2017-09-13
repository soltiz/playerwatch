from sys import argv
from base64 import b64encode
from datetime import datetime

# This is for Python 2
from hashlib import sha1
import hmac
def create_signature(secret_key, string):
    string_to_sign = string.encode('utf-8')
    hashed = hmac.new(secret_key,string_to_sign, sha1)
    return hashed.hexdigest()

def create_token(access_key):
    string_to_sign = "POST\n"+\
                     "application/x-www-form-urlencoded\n"+\
                     datetime.utcnow().strftime("%Y-%m-%dT%H:%M")
    user_secret_key = access_key # Should be looked up based on access_key
    hmac = create_signature(access_key, string_to_sign)
    signature = "AUTH:" + access_key + ":" + hmac
    return signature

def authenticate_signed_token(auth_token):
    """ Take token, recreate signature, auth if a match """
    lead, access_key, signature = auth_token.split(":")
    if lead.upper() == "AUTH":
        our_token = create_token(access_key).split(":", 1)[-1]
    return True if signature == our_token else False


if __name__ == "__main__":
    print create_token('secret_api_key')
    print authenticate_signed_token(argv[1])
