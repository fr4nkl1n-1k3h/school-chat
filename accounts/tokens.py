import random
import string
from django.contrib.auth import get_user_model
from .models import TokenActivation




def account_activation_token():
    length = 100
    return ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k = length ))



User = get_user_model()



def check_token(user, token):
    check_token = TokenActivation.objects.filter(user_id=user,token=token)
    print(check_token)
    if check_token.count() <= 0:
        return False
    check_token.delete()
    return True