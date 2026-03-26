from django.db import models

from .station_meteo import StationMeteo


class DonneesMeteo(models.Model):
    """
    Données météo quotidiennes issues de l'API MétéoFrance DPClim.
    Alimentées via la commande : make fetch-meteo TOKEN=<token> STATION_ID=<id> START=<YYYY-MM-DD> STOP=<YYYY-MM-DD>

    Les champs correspondent aux colonnes du CSV retourné par l'API DPClim quotidienne.
    Les données brutes (toutes colonnes) sont également stockées au format JSON.
    """

    station = models.ForeignKey(
        StationMeteo,
        on_delete=models.CASCADE,
        related_name="donnees",
        verbose_name="Station météo",
    )
    date = models.DateField(
        verbose_name="Date",
    )

    # Précipitations
    precipitation = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Précipitations (mm) – RR",
    )

    # Températures
    temperature_min = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Température minimale (°C) – TN",
    )
    temperature_max = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Température maximale (°C) – TX",
    )
    temperature_moyenne = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Température moyenne (°C) – TM",
    )

    # Vent
    vent_moyen = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Vent moyen quotidien (m/s) – FFM",
    )
    vent_rafale_max = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Rafale maximale (m/s) – FXY",
    )

    # Ensoleillement / neige
    ensoleillement = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Durée d'insolation (h) – INST",
    )
    hauteur_neige = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Hauteur de neige (cm) – HN",
    )

    # Toutes les autres colonnes brutes du CSV
    donnees_brutes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Données brutes (JSON)",
    )

    class Meta:
        verbose_name = "Données météo"
        verbose_name_plural = "Données météo"
        ordering = ["station", "date"]
        unique_together = ("station", "date")

    def __str__(self):
        return f"{self.station} – {self.date}"
