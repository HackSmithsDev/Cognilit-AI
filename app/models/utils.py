# import uuid
import secrets

# not used anymore
# def generate_uuid():
#     return str(uuid.uuid4())

def generate_secret_id():
    # 20 character long
    return secrets.token_urlsafe(15)