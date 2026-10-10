import secrets

from .models import Client


def generate_client_number():
    """Numéro client unique : « CL » + 8 chiffres."""
    while True:
        number = "CL" + "".join(secrets.choice("0123456789") for _ in range(8))
        if not Client.objects.filter(client_number=number).exists():
            return number
