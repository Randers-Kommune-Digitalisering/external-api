import requests
import jwt
import logging
from functools import wraps
from cryptography.hazmat.primitives import serialization
from flask import Response, request
from base64 import b64decode


logger = logging.getLogger(__name__)


class AuthorizationHelper:
    def __init__(self, keycloak_url, realm, audience):
        self.algorithms = ["RS256"]
        self.audience = audience
        self.url = f"{keycloak_url}auth/realms/{realm}/"
        self.public_key = self.get_public_key()

    def get_public_key(self):
        try:
            r = requests.get(self.url)
            r.raise_for_status()
            key_der_base64 = r.json()["public_key"]
            key_der = b64decode(key_der_base64.encode())
            return serialization.load_der_public_key(key_der)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch public key from Keycloak: {e}")
            return None

    def decode_token(self, token):
        try:
            if not self.public_key:
                self.public_key = self.get_public_key()
                if not self.public_key:
                    logger.error('No public key - cannot verify tokens')
                    return None

            payload = jwt.decode(token, self.public_key, audience=self.audience, algorithms=self.algorithms)
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidAudienceError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    # Decorator - checks token
    def authorization(self, f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                token_header = request.headers.get('Authorization')
                if not token_header:
                    return Response(status=401, response="Unauthorized")
                else:
                    token = token_header.split()[1]
                    if self.decode_token(token):
                        return f(*args, **kwargs)
                    else:
                        logger.warning("Decode token returned nothing")
                        return Response(status=401, response="Unauthorized")
            except Exception as e:
                logger.error(e)
                return Response(status=401, response=str(e))
        return decorated_function
