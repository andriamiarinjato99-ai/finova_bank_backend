from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from apps.accounts.models import BankAccount
from apps.agencies.models import Agency
from apps.clients.models import Client
from .services import deposit, transfer, withdraw


def make_customer(username, number, account_number, agency):
    """Crée un utilisateur non-staff avec sa fiche client et un compte."""
    user = User.objects.create_user(username=username, password="testpass123")
    client = Client.objects.create(
        user=user, client_number=number, first_name=username, last_name="Test",
        email=f"{username}@test.local", phone="0340000000",
    )
    account = BankAccount.objects.create(account_number=account_number, client=client, agency=agency)
    return user, account


class BankingServiceTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="staff", password="testpass123", is_staff=True)
        agency = Agency.objects.create(code="TEST", name="Test", address="Test")
        self.alice, self.a1 = make_customer("alice", "C1", "A001", agency)
        self.bob, self.a2 = make_customer("bob", "C2", "A002", agency)

    def test_deposit_and_withdraw(self):
        deposit(self.a1.id, "1000", self.alice)
        self.a1.refresh_from_db()
        self.assertEqual(self.a1.balance, Decimal("1000.00"))
        withdraw(self.a1.id, "250", self.alice)
        self.a1.refresh_from_db()
        self.assertEqual(self.a1.balance, Decimal("750.00"))

    def test_withdraw_more_than_balance_is_refused(self):
        deposit(self.a1.id, "100", self.alice)
        with self.assertRaises(ValidationError):
            withdraw(self.a1.id, "500", self.alice)
        self.a1.refresh_from_db()
        self.assertEqual(self.a1.balance, Decimal("100.00"))

    def test_customer_can_transfer_to_another_customer(self):
        deposit(self.a1.id, "1000", self.alice)
        transfer(self.a1.id, self.a2.id, "400", self.alice)
        self.a1.refresh_from_db()
        self.a2.refresh_from_db()
        self.assertEqual(self.a1.balance, Decimal("600.00"))
        self.assertEqual(self.a2.balance, Decimal("400.00"))

    def test_customer_cannot_debit_someone_elses_account(self):
        deposit(self.a2.id, "1000", self.bob)
        with self.assertRaises(ValidationError):
            transfer(self.a2.id, self.a1.id, "400", self.alice)
        self.a2.refresh_from_db()
        self.assertEqual(self.a2.balance, Decimal("1000.00"))

    def test_customer_cannot_deposit_on_someone_elses_account(self):
        with self.assertRaises(ValidationError):
            deposit(self.a2.id, "100", self.alice)

    def test_staff_transfer_is_balanced(self):
        deposit(self.a1.id, "1000", self.staff)
        transfer(self.a1.id, self.a2.id, "400", self.staff)
        self.a1.refresh_from_db()
        self.a2.refresh_from_db()
        self.assertEqual(self.a1.balance + self.a2.balance, Decimal("1000.00"))


class ApiFlowTests(APITestCase):
    """Parcours complet : inscription -> connexion -> dépôt -> retrait -> bénéficiaire -> virement."""

    def register(self, email, password="Secret2026x", first="Test", last="User"):
        return self.client.post(
            "/api/auth/register/",
            {"first_name": first, "last_name": last, "email": email, "phone": "0341234567", "password": password},
            format="json",
        )

    def login(self, email, password="Secret2026x"):
        response = self.client.post("/api/auth/token/", {"username": email, "password": password}, format="json")
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def first_account(self):
        response = self.client.get("/api/accounts/")
        self.assertEqual(response.status_code, 200)
        return response.data["results"][0]

    def test_register_creates_client_and_account(self):
        response = self.register("new@test.local")
        self.assertEqual(response.status_code, 201)
        self.login("new@test.local")
        me = self.client.get("/api/clients/me/")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["email"], "new@test.local")
        account = self.first_account()
        self.assertEqual(Decimal(account["balance"]), Decimal("0.00"))
        self.assertTrue(account["account_number"].startswith("MG"))

    def test_register_rejects_duplicate_email_and_weak_password(self):
        self.assertEqual(self.register("dup@test.local").status_code, 201)
        self.assertEqual(self.register("DUP@test.local").status_code, 400)
        self.assertEqual(self.register("weak@test.local", password="123").status_code, 400)

    def test_deposit_withdraw_and_transfer_between_two_users(self):
        self.register("alice@test.local")
        self.register("bob@test.local")

        self.login("bob@test.local")
        bob_account = self.first_account()

        self.login("alice@test.local")
        alice_account = self.first_account()

        # Dépôt puis retrait trop élevé (refusé) puis retrait valide
        deposit_resp = self.client.post(
            "/api/transactions/deposit/", {"account_id": alice_account["id"], "amount": "1000.00"}, format="json"
        )
        self.assertEqual(deposit_resp.status_code, 201)
        too_much = self.client.post(
            "/api/transactions/withdraw/", {"account_id": alice_account["id"], "amount": "5000.00"}, format="json"
        )
        self.assertEqual(too_much.status_code, 400)
        ok = self.client.post(
            "/api/transactions/withdraw/", {"account_id": alice_account["id"], "amount": "200.00"}, format="json"
        )
        self.assertEqual(ok.status_code, 201)

        # Bénéficiaire = numéro de compte de Bob ; l'API retrouve l'identifiant du compte
        ben = self.client.post(
            "/api/beneficiaries/",
            {"name": "Bob", "account_number": bob_account["account_number"], "bank_name": "Finova"},
            format="json",
        )
        self.assertEqual(ben.status_code, 201)
        self.assertEqual(ben.data["account_id"], bob_account["id"])

        # Virement vers Bob
        transfer_resp = self.client.post(
            "/api/transactions/transfer/",
            {"source_account_id": alice_account["id"], "destination_account_id": ben.data["account_id"], "amount": "300.00"},
            format="json",
        )
        self.assertEqual(transfer_resp.status_code, 201)
        self.assertEqual(transfer_resp.data["direction"], "OUT")
        self.assertEqual(Decimal(self.first_account()["balance"]), Decimal("500.00"))

        # Bob voit le virement reçu et son solde a augmenté
        self.login("bob@test.local")
        self.assertEqual(Decimal(self.first_account()["balance"]), Decimal("300.00"))
        history = self.client.get("/api/transactions/")
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.data["count"], 1)
        self.assertEqual(history.data["results"][0]["direction"], "IN")

        # Bob ne peut pas débiter le compte d'Alice
        forbidden = self.client.post(
            "/api/transactions/transfer/",
            {"source_account_id": alice_account["id"], "destination_account_id": bob_account["id"], "amount": "10.00"},
            format="json",
        )
        self.assertEqual(forbidden.status_code, 400)

    def test_customer_can_open_account_but_not_edit_balance(self):
        self.register("carol@test.local")
        self.login("carol@test.local")
        created = self.client.post("/api/accounts/", {"account_type": "SAVINGS", "currency": "EUR"}, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data["account_type"], "SAVINGS")
        self.assertEqual(created.data["currency"], "EUR")
        patch = self.client.patch(f"/api/accounts/{created.data['id']}/", {"status": "CLOSED"}, format="json")
        self.assertEqual(patch.status_code, 403)

    def test_customer_cannot_list_other_clients_or_employees(self):
        self.register("dave@test.local")
        self.register("erin@test.local")
        self.login("dave@test.local")
        clients = self.client.get("/api/clients/")
        self.assertEqual(clients.data["count"], 1)
        self.assertEqual(self.client.get("/api/employees/").status_code, 403)
        self.assertEqual(self.client.post("/api/agencies/", {"code": "X", "name": "X", "address": "X"}, format="json").status_code, 403)
