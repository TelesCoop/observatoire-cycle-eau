"""
Commande Django pour récupérer la liste des stations météo depuis l'API MétéoFrance DPClim
et les stocker en base de données.

Usage :
    python manage.py fetch_stations --token <TOKEN> [--departement 17]

Ou via le Makefile :
    make fetch-stations TOKEN=<TOKEN>
    make fetch-stations TOKEN=<TOKEN> DEPT=34

Le token est valable 1h – il doit être régénéré manuellement depuis
https://portail-api.meteofrance.fr/ avant chaque exécution.
"""

import requests
from django.core.management.base import BaseCommand, CommandError

from observatoire.models.station_meteo import StationMeteo

DPCLIM_BASE_URL = "https://public-api.meteofrance.fr/public/DPClim/v1"


class Command(BaseCommand):
    help = (
        "Récupère la liste des stations météo DPClim pour un département "
        "et les stocke en base de données SQLite."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--token",
            type=str,
            required=True,
            help="Bearer token d'accès à l'API MétéoFrance (valable 1h).",
        )
        parser.add_argument(
            "--departement",
            type=str,
            default="17",
            help="Numéro de département (défaut : 17).",
        )

    def handle(self, *args, **options):
        token = options["token"]
        departement = options["departement"]

        url = f"{DPCLIM_BASE_URL}/liste-stations/quotidienne"
        params = {"id-departement": departement}
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        self.stdout.write(
            f"Récupération des stations pour le département {departement}…"
        )

        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            raise CommandError(
                f"Erreur HTTP {response.status_code} lors de l'appel à l'API : {exc}\n"
                f"Réponse : {response.text}"
            )
        except requests.exceptions.RequestException as exc:
            raise CommandError(f"Erreur réseau : {exc}")

        stations_data = response.json()
        self.stdout.write(f"{len(stations_data)} station(s) reçue(s) de l'API.")

        created_count = 0
        updated_count = 0

        for station in stations_data:
            obj, created = StationMeteo.objects.update_or_create(
                id_station=station["id"],
                defaults={
                    "nom": station.get("nom", ""),
                    "poste_ouvert": station.get("posteOuvert", False),
                    "type_poste": station.get("typePoste"),
                    "lon": station.get("lon"),
                    "lat": station.get("lat"),
                    "alt": station.get("alt"),
                    "poste_public": station.get("postePublic", False),
                    "departement": departement,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Terminé – {created_count} station(s) créée(s), "
                f"{updated_count} station(s) mise(s) à jour."
            )
        )

        open_count = StationMeteo.objects.filter(
            departement=departement, poste_ouvert=True
        ).count()
        self.stdout.write(
            f"Stations ouvertes (posteOuvert=True) pour le département {departement} "
            f": {open_count}"
        )
