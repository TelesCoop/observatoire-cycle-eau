"""
Commande Django pour récupérer les données météo quotidiennes depuis l'API MétéoFrance
DPClim pour une station donnée et les stocker en base de données.

C'est la traduction Python du script scripts/station-meteo.bash.

Usage :
    python manage.py fetch_meteo_data --token <TOKEN> --station-id <STATION_ID>
                                      --start <YYYY-MM-DD> [--stop <YYYY-MM-DD>]

Ou via le Makefile :
    make fetch-meteo TOKEN=<TOKEN> STATION_ID=<STATION_ID> START=<YYYY-MM-DD>
    make fetch-meteo TOKEN=<TOKEN> STATION_ID=<STATION_ID> START=<YYYY-MM-DD> STOP=<YYYY-MM-DD>

Le token est valable 1h – il doit être régénéré manuellement depuis
https://portail-api.meteofrance.fr/ avant chaque exécution.

L'API DPClim ne permet de récupérer qu'une année de données à la fois ;
la commande découpe automatiquement la plage en tranches de 365 jours.
"""

import csv
import io
import time
from datetime import date, datetime, timedelta

import requests
from django.core.management.base import BaseCommand, CommandError

from observatoire.models.donnees_meteo import DonneesMeteo
from observatoire.models.station_meteo import StationMeteo

DPCLIM_BASE_URL = "https://public-api.meteofrance.fr/public/DPClim/v1"
CHUNK_DAYS = 365  # Limite de l'API : 1 an par requête
# Délai entre les tentatives de récupération du fichier (l'API est asynchrone)
POLL_INTERVAL_SECONDS = 2
MAX_POLL_ATTEMPTS = 15

# Correspondance colonnes CSV → champs du modèle DonneesMeteo
CSV_FIELD_MAP = {
    "RR": "precipitation",
    "TN": "temperature_min",
    "TX": "temperature_max",
    "TM": "temperature_moyenne",
    "FFM": "vent_moyen",
    "FXY": "vent_rafale_max",
    "INST": "ensoleillement",
    "HN": "hauteur_neige",
}


def _parse_float(value: str):
    """Convertit une chaîne en float, renvoie None si vide ou non numérique."""
    value = value.strip()
    if value in ("", "mq", "nan"):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_date(aaaammjj: str) -> date:
    """Convertit une date au format AAAAMMJJ en objet date Python."""
    return datetime.strptime(aaaammjj.strip(), "%Y%m%d").date()


class Command(BaseCommand):
    help = (
        "Récupère les données météo quotidiennes DPClim pour une station "
        "et les stocke en base de données SQLite. "
        "Traduction Python du script scripts/station-meteo.bash."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--token",
            type=str,
            required=True,
            help="Bearer token d'accès à l'API MétéoFrance (valable 1h).",
        )
        parser.add_argument(
            "--station-id",
            type=str,
            required=True,
            help=(
                "Identifiant de la station météo (ex : 17300001). "
                "Récupérer la liste avec : make fetch-stations TOKEN=<TOKEN>"
            ),
        )
        parser.add_argument(
            "--start",
            type=str,
            required=True,
            help="Date de début au format YYYY-MM-DD.",
        )
        parser.add_argument(
            "--stop",
            type=str,
            default=None,
            help=(
                "Date de fin au format YYYY-MM-DD. "
                "Si absente ou dans le futur, la date d'aujourd'hui est utilisée."
            ),
        )

    def handle(self, *args, **options):
        token = options["token"]
        station_id = options["station_id"]
        start_str = options["start"]
        stop_str = options["stop"]

        # --- Validation et normalisation des dates ---
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        except ValueError:
            raise CommandError(
                f"Format de date invalide pour --start : '{start_str}'. "
                "Attendu : YYYY-MM-DD"
            )

        today = date.today()

        if stop_str:
            try:
                stop_date = datetime.strptime(stop_str, "%Y-%m-%d").date()
            except ValueError:
                raise CommandError(
                    f"Format de date invalide pour --stop : '{stop_str}'. "
                    "Attendu : YYYY-MM-DD"
                )
            # Comme dans le script bash : si stop > aujourd'hui → aujourd'hui
            if stop_date > today:
                self.stdout.write(
                    f"La date de fin ({stop_date}) est dans le futur – "
                    f"utilisation de la date d'aujourd'hui ({today})."
                )
                stop_date = today
        else:
            stop_date = today

        if start_date > stop_date:
            raise CommandError(
                f"La date de début ({start_date}) est postérieure "
                f"à la date de fin ({stop_date})."
            )

        # --- Vérification de la station en base ---
        try:
            station = StationMeteo.objects.get(id_station=station_id)
        except StationMeteo.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(
                    f"La station {station_id} n'existe pas encore en base de données. "
                    "Elle sera créée à la volée. "
                    "Pensez à exécuter 'make fetch-stations TOKEN=<TOKEN>' au préalable."
                )
            )
            station = StationMeteo.objects.create(
                id_station=station_id,
                nom=f"Station {station_id}",
            )

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "*/*",
            "User-Agent": (
                "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:135.0) "
                "Gecko/20100101 Firefox/135.0"
            ),
        }

        # --- Boucle par tranches de 365 jours (limite API) ---
        chunk_start = start_date
        total_created = 0
        total_updated = 0
        is_first_chunk = True

        while chunk_start <= stop_date:
            chunk_stop = min(
                chunk_start + timedelta(days=CHUNK_DAYS - 1),
                stop_date,
            )

            self.stdout.write(
                f"Traitement de la tranche {chunk_start} → {chunk_stop}…"
            )

            csv_text = self._fetch_chunk(
                station_id=station_id,
                chunk_start=chunk_start,
                chunk_stop=chunk_stop,
                headers=headers,
            )

            created, updated = self._save_csv(
                csv_text=csv_text,
                station=station,
                skip_header=not is_first_chunk,
            )
            total_created += created
            total_updated += updated

            self.stdout.write(
                f"  → {created} enregistrement(s) créé(s), "
                f"{updated} mis à jour."
            )

            chunk_start = chunk_stop + timedelta(days=1)
            is_first_chunk = False

        self.stdout.write(
            self.style.SUCCESS(
                f"Terminé – {total_created} enregistrement(s) créé(s), "
                f"{total_updated} mis à jour pour la station {station_id}."
            )
        )

    # ------------------------------------------------------------------
    # Méthodes internes
    # ------------------------------------------------------------------

    def _fetch_chunk(
        self,
        station_id: str,
        chunk_start: date,
        chunk_stop: date,
        headers: dict,
    ) -> str:
        """
        Commande une tranche de données auprès de l'API DPClim puis
        télécharge le fichier CSV résultant.

        Reproduit la logique du script bash :
          1. GET /commande-station/quotidienne  → obtient un id de commande
          2. GET /commande/fichier?id-cmde=...  → télécharge le CSV
        """
        # Étape 1 : passer la commande
        commande_url = f"{DPCLIM_BASE_URL}/commande-station/quotidienne"
        params = {
            "id-station": station_id,
            "date-deb-periode": f"{chunk_start.strftime('%Y-%m-%d')}T00:00:00Z",
            "date-fin-periode": f"{chunk_stop.strftime('%Y-%m-%d')}T00:00:00Z",
        }

        try:
            resp = requests.get(
                commande_url, params=params, headers=headers, timeout=30
            )
            resp.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            raise CommandError(
                f"Erreur HTTP lors de la commande de données "
                f"({chunk_start} → {chunk_stop}) : {exc}\n"
                f"Réponse : {resp.text}"
            )
        except requests.exceptions.RequestException as exc:
            raise CommandError(f"Erreur réseau lors de la commande : {exc}")

        data = resp.json()
        try:
            file_id = data["elaboreProduitAvecDemandeResponse"]["return"]
        except (KeyError, TypeError) as exc:
            raise CommandError(
                f"Réponse inattendue de l'API (commande) : {data}\n"
                f"Détail : {exc}"
            )

        # Étape 2 : télécharger le fichier (l'API peut nécessiter quelques
        # secondes pour générer le fichier → on réessaie si nécessaire)
        fichier_url = f"{DPCLIM_BASE_URL}/commande/fichier"
        fichier_params = {"id-cmde": file_id}

        for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
            try:
                file_resp = requests.get(
                    fichier_url,
                    params=fichier_params,
                    headers=headers,
                    timeout=60,
                )
                if file_resp.status_code == 204:
                    # Fichier pas encore prêt
                    self.stdout.write(
                        f"  Fichier pas encore prêt (tentative {attempt}/"
                        f"{MAX_POLL_ATTEMPTS}), attente {POLL_INTERVAL_SECONDS}s…"
                    )
                    time.sleep(POLL_INTERVAL_SECONDS)
                    continue
                file_resp.raise_for_status()
                break
            except requests.exceptions.HTTPError as exc:
                raise CommandError(
                    f"Erreur HTTP lors du téléchargement du fichier : {exc}\n"
                    f"Réponse : {file_resp.text}"
                )
            except requests.exceptions.RequestException as exc:
                raise CommandError(
                    f"Erreur réseau lors du téléchargement du fichier : {exc}"
                )
        else:
            raise CommandError(
                f"Le fichier {file_id} n'est pas disponible après "
                f"{MAX_POLL_ATTEMPTS} tentatives."
            )

        # Reproduit le sed 's/,/./g' du script bash :
        # l'API renvoie des valeurs décimales avec une virgule comme séparateur
        csv_text = file_resp.text.replace(",", ".")
        return csv_text

    def _save_csv(
        self,
        csv_text: str,
        station: StationMeteo,
        skip_header: bool = False,
    ):
        """
        Parse le CSV et insère / met à jour les enregistrements en base.

        Le CSV est délimité par des points-virgules.
        Si skip_header=True, la première ligne (en-tête) est ignorée
        (comportement identique au `tail -n +2` du script bash pour les
        tranches suivantes à la première).
        """
        created_count = 0
        updated_count = 0

        reader = csv.DictReader(
            io.StringIO(csv_text), delimiter=";"
        )

        for row in reader:
            # Date – colonne AAAAMMJJ
            date_str = row.get("AAAAMMJJ", "").strip()
            if not date_str:
                continue
            try:
                record_date = _parse_date(date_str)
            except ValueError:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Date invalide ignorée : '{date_str}'"
                    )
                )
                continue

            # Champs principaux
            model_fields = {
                field_name: _parse_float(row.get(csv_col, ""))
                for csv_col, field_name in CSV_FIELD_MAP.items()
            }

            # Données brutes : toutes les colonnes du CSV
            donnees_brutes = {k: v for k, v in row.items()}

            obj, created = DonneesMeteo.objects.update_or_create(
                station=station,
                date=record_date,
                defaults={
                    **model_fields,
                    "donnees_brutes": donnees_brutes,
                },
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        return created_count, updated_count
