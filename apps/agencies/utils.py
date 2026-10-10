from .models import Agency

DEFAULT_AGENCY_CODE = "AG001"


def get_default_agency():
    """Agence par défaut utilisée pour les comptes ouverts en ligne."""
    agency, _ = Agency.objects.get_or_create(
        code=DEFAULT_AGENCY_CODE,
        defaults={"name": "Agence Centrale", "address": "Antananarivo"},
    )
    return agency
