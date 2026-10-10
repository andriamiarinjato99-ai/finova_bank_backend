import secrets

from .models import BankAccount


def generate_account_number():
    """Numéro de compte unique : « MG » + 18 chiffres."""
    while True:
        number = "MG" + "".join(secrets.choice("0123456789") for _ in range(18))
        if not BankAccount.objects.filter(account_number=number).exists():
            return number
