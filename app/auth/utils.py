import secrets

def generate_auth_code():
    return str(secrets.randbelow(900000) + 100000)