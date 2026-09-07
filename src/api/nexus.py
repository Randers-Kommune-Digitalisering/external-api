import logging
from flask import Response, request, Blueprint
from datetime import datetime
from utils.openid_integration import authorization_helper
from handlers.nexus import HJAELPEMIDDEL_HANDLERS
from utils.utils import danish_to_ascii

logger = logging.getLogger(__name__)
nexus_bp = Blueprint('nexus', __name__, url_prefix='/nexus')


@nexus_bp.post('/hjaelpemiddel')
@authorization_helper.authorization
def post_hjaelpemiddel_to_db():
    if not request.is_json:
        return Response('Request body must be JSON', status=400)

    data = request.get_json()
    required_keys = {"cpr", "formName", "formData", "attachments", "date"}
    missing_keys = sorted(required_keys - set(data or {}))
    if missing_keys:
        return Response(f"Missing required keys: {', '.join(missing_keys)}", status=400)

    try:
        datetime.fromisoformat(data["date"].replace("Z", "+00:00")).date()
    except (AttributeError, TypeError, ValueError):
        return Response('Invalid date format; expected ISO 8601 date or datetime', status=400)

    # When xFlow attaches a 'blanket' to an email it replaces spaces with underscores and removes hyphens, as well as transforms Danish characters. So the pattern is matched here.
    form_name = danish_to_ascii(data['formName'].replace(" ", "_").replace("-", "")).lower()
    if form_name not in HJAELPEMIDDEL_HANDLERS:
        return Response(f"Form name '{form_name}' is not allowed", status=400)
    else:
        is_added_to_db = HJAELPEMIDDEL_HANDLERS[form_name](data)
        if not is_added_to_db:
            return Response(f"Failed to add form '{form_name}' to the database", status=500)
        return Response(f"Form '{form_name}' successfully added to the database", status=200)
