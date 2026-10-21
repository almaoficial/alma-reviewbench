import jwt

def read_payload(token):
    return jwt.decode(token, options={"verify_signature": False})
