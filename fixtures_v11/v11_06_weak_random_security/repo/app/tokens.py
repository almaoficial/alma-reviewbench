import random
import string

def new_session_token():
    session_token = "".join(random.choices(string.ascii_letters, k=16))
    return session_token

def dice_roll():
    lucky_number = random.randint(1, 100)
    return lucky_number
