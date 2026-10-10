from decimal import Decimal
from uuid import uuid4
from django.db import transaction
from rest_framework.exceptions import ValidationError
from apps.accounts.models import BankAccount
from apps.audit.models import AuditLog
from .models import Transaction

def _reference(prefix):
    return f"{prefix}-{uuid4().hex[:16].upper()}"


def _get_owned_account(account_id, user):
    qs = BankAccount.objects.select_for_update()
    if not user.is_staff:
        qs = qs.filter(client__user=user)
    try:
        return qs.get(pk=account_id)
    except BankAccount.DoesNotExist:
        raise ValidationError("Compte introuvable ou non autorisé.")

@transaction.atomic
def deposit(account_id, amount, user, description=""):
    amount = Decimal(str(amount))
    if amount <= 0:
        raise ValidationError("Le montant doit être supérieur à 0.")

    account = _get_owned_account(account_id, user)
    if account.status != BankAccount.Status.ACTIVE:
        raise ValidationError("Le compte n'est pas actif.")

    account.balance += amount
    account.save(update_fields=["balance"])

    tx = Transaction.objects.create(
        reference=_reference("DEP"),
        transaction_type=Transaction.Type.DEPOSIT,
        destination_account=account,
        amount=amount,
        currency=account.currency,
        description=description,
        performed_by=user,
    )
    AuditLog.objects.create(
        user=user, action=AuditLog.Action.DEPOSIT, entity="BankAccount",
        entity_id=str(account.pk),
        description=f"Dépôt de {amount} {account.currency} sur {account.account_number}",
    )
    return tx

@transaction.atomic
def withdraw(account_id, amount, user, description=""):
    amount = Decimal(str(amount))
    if amount <= 0:
        raise ValidationError("Le montant doit être supérieur à 0.")

    account = _get_owned_account(account_id, user)
    if account.status != BankAccount.Status.ACTIVE:
        raise ValidationError("Le compte n'est pas actif.")
    if account.balance < amount:
        raise ValidationError("Solde insuffisant.")

    account.balance -= amount
    account.save(update_fields=["balance"])

    tx = Transaction.objects.create(
        reference=_reference("WDL"),
        transaction_type=Transaction.Type.WITHDRAW,
        source_account=account,
        amount=amount,
        currency=account.currency,
        description=description,
        performed_by=user,
    )
    AuditLog.objects.create(
        user=user, action=AuditLog.Action.WITHDRAW, entity="BankAccount",
        entity_id=str(account.pk),
        description=f"Retrait de {amount} {account.currency} depuis {account.account_number}",
    )
    return tx

@transaction.atomic
def transfer(source_account_id, destination_account_id, amount, user, description=""):
    """
    Virement d'un compte à un autre.
    - le compte source doit appartenir à l'utilisateur (sauf personnel) ;
    - le compte destinataire peut appartenir à n'importe quel client (virement vers un tiers).
    """
    amount = Decimal(str(amount))
    if amount <= 0:
        raise ValidationError("Le montant doit être supérieur à 0.")
    source_id, destination_id = int(source_account_id), int(destination_account_id)
    if source_id == destination_id:
        raise ValidationError("Le compte source et le compte destination doivent être différents.")

    # Ordre déterministe des verrous pour limiter les risques de deadlock.
    first_id, second_id = sorted([source_id, destination_id])
    locked = {a.pk: a for a in BankAccount.objects.select_for_update().filter(pk__in=[first_id, second_id])}
    source = locked.get(source_id)
    destination = locked.get(destination_id)
    if source is None:
        raise ValidationError("Compte source introuvable ou non autorisé.")
    if destination is None:
        raise ValidationError("Compte destinataire introuvable.")
    if not user.is_staff and source.client.user_id != user.id:
        raise ValidationError("Compte source introuvable ou non autorisé.")

    if source.status != BankAccount.Status.ACTIVE:
        raise ValidationError("Le compte source n'est pas actif.")
    if destination.status != BankAccount.Status.ACTIVE:
        raise ValidationError("Le compte destinataire n'est pas actif.")
    if source.currency != destination.currency:
        raise ValidationError("Les devises des comptes doivent être identiques.")
    if source.balance < amount:
        raise ValidationError("Solde insuffisant.")

    source.balance -= amount
    destination.balance += amount
    source.save(update_fields=["balance"])
    destination.save(update_fields=["balance"])

    tx = Transaction.objects.create(
        reference=_reference("TRF"),
        transaction_type=Transaction.Type.TRANSFER,
        source_account=source,
        destination_account=destination,
        amount=amount,
        currency=source.currency,
        description=description,
        performed_by=user,
    )
    AuditLog.objects.create(
        user=user, action=AuditLog.Action.TRANSFER, entity="Transaction",
        entity_id=str(tx.pk),
        description=f"Virement de {amount} {source.currency}: {source.account_number} -> {destination.account_number}",
    )
    return tx
