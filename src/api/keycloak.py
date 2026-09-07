import requests
import logging

from flask import Blueprint, Response, request, jsonify

from utils.openid_integration import authorization_helper
from utils.config import KEYCLOAK_URL, KEYCLOAK_REALM, KEYCLOAK_USER_ADMIN_CLIENT_ID, KEYCLOAK_USER_ADMIN_CLIENT_SECRET
from utils.token_provider import BearerAuth


logger = logging.getLogger(__name__)
keycloak_bp = Blueprint("keycloak", __name__, url_prefix="/keycloak")


@keycloak_bp.post("/add-user-to-group")
@authorization_helper.authorization
def add_user_to_group():
    data = request.get_json()
    if not data or 'email' not in data or 'group' not in data:
        return Response('Missing required keys: email and group', status=400)

    keycloak_url = KEYCLOAK_URL.strip()
    if not keycloak_url.startswith(("http://", "https://")):
        keycloak_url = "https://" + keycloak_url
    if not keycloak_url.endswith("/"):
        keycloak_url += "/"

    session = requests.Session()
    session.auth = BearerAuth(
        token_url=f"{keycloak_url}auth/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token",
        client_id=KEYCLOAK_USER_ADMIN_CLIENT_ID,
        client_secret=KEYCLOAK_USER_ADMIN_CLIENT_SECRET
    )

    user_added = False
    message = "Der er desværre sket en fejl i forbindelse med tildeling af rettigheder. For at få rettet op på dette bedes I venligst videresende denne mail til digitalisering@randers.dk."
    error = None

    try:
        user_res = session.get(f"{keycloak_url}auth/admin/realms/{KEYCLOAK_REALM}/users", params={'email': data['email']})
        user_res.raise_for_status()
        users = user_res.json()

        group_res = session.get(f"{keycloak_url}auth/admin/realms/{KEYCLOAK_REALM}/groups", params={'search': data['group']})
        group_res.raise_for_status()
        groups_found = group_res.json()

        if len(users) != 1:
            logger.error(f"User search returned {len(users)} results for email: {data['email']}")
            return jsonify({"user_added": False, "message": message, "error": "User not found or multiple matches"}), 200
        
        user_id = users[0]['id']

        target_group = next((g for g in groups_found if g['name'] == data['group']), None)
        
        if not target_group:
            logger.error(f"Group '{data['group']}' was not found in Keycloak search results.")
            return jsonify({"user_added": False, "message": message, "error": f"Exact group '{data['group']}' not found"}), 200
        
        group_id = target_group['id']

        res = session.put(f"{keycloak_url}auth/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/groups/{group_id}")
        res.raise_for_status()
        
        user_added = True
        message = "Du har nu fået tildelt de ønskede rettigheder."

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Keycloak HTTP error: {http_err} - Response: {http_err.response.text if http_err.response else ''}")
        error = f"HTTP error: {str(http_err)}"
    except Exception as e:
        logger.error(f"Failed to add user to group: {e}")
        error = str(e)

    return jsonify({"user_added": user_added, "message": message, "error": error}), 200
