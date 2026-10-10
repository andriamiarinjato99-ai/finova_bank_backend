# Finova — backend Django REST

API de gestion bancaire : clients, comptes, dépôts, retraits, virements, bénéficiaires, journal d'audit.

## Installation

```bash
python -m venv venv
# Windows : venv\Scripts\activate      macOS / Linux : source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # Windows : copy .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Sous Windows, `setup.bat` enchaîne ces étapes.

- Swagger : http://127.0.0.1:8000/api/docs/ · Schéma OpenAPI : http://127.0.0.1:8000/api/schema/
- Administration : http://127.0.0.1:8000/admin/ (`admin` / `Admin123!`)
- Clients de démonstration : `jean@finova.mg` et `hery@finova.mg` (mot de passe `Demo12345!`)

Configuration (`.env`) : `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`. Changez `SECRET_KEY` et les mots de passe de démonstration hors développement.

## Routes principales

```text
POST /api/auth/register/              Inscription publique (utilisateur + client + premier compte)
POST /api/auth/token/                 Connexion { username, password } -> { access, refresh }
POST /api/auth/token/refresh/

GET  /api/clients/me/                 Fiche du client connecté
GET/PATCH /api/clients/{id}/          Un client modifie son e-mail, téléphone et adresse
GET/POST  /api/accounts/              Ses comptes ; POST { account_type, currency } ouvre un compte
GET/POST/PATCH/DELETE /api/beneficiaries/   Ses bénéficiaires (champ account_id résolu côté serveur)
GET  /api/agencies/                   Lecture pour tous, écriture réservée au personnel

GET  /api/transactions/               Historique paginé (opérations émises et reçues), filtres, tri
POST /api/transactions/deposit/       { account_id, amount, description }
POST /api/transactions/withdraw/      { account_id, amount, description }
POST /api/transactions/transfer/      { source_account_id, destination_account_id, amount, description }

GET  /api/statistics/                 Statistiques du client (ou globales pour le personnel)
GET  /api/employees/, /api/audit/     Réservé au personnel
```

Les listes sont paginées (`count`, `next`, `previous`, `results`, 20 éléments par page).

## Règles métier

- Un client ne voit et ne modifie que ses propres données ; clients, agences, employés et audit sont gérés par le personnel.
- Dépôt et retrait : uniquement sur ses comptes, montant > 0, compte actif, solde suffisant pour un retrait.
- Virement : depuis un de ses comptes vers n'importe quel compte actif de même devise ; opération atomique avec verrouillage des deux comptes.
- Chaque transaction renvoie `direction` (`IN`, `OUT` ou `INTERNAL`) selon l'utilisateur connecté.
- Un client peut ouvrir jusqu'à 5 comptes ; le numéro, l'agence et le propriétaire sont attribués par le serveur.

## Tests

```bash
python manage.py test
```

## Architecture

```text
apps/clients        clients, inscription (auth.py)
apps/accounts       comptes bancaires
apps/transactions   dépôts, retraits, virements (services.py)
apps/beneficiaries  bénéficiaires
apps/agencies       agences
apps/employees      employés et rôles
apps/audit          journal d'audit
apps/dashboard      statistiques
```
