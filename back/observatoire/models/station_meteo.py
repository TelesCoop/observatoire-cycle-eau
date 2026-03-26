from django.db import models


class StationMeteo(models.Model):
    """
    Station météorologique issue de l'API MétéoFrance DPClim.
    Alimentée via la commande : make fetch-stations TOKEN=<token>
    """

    id_station = models.CharField(
        max_length=20,
        primary_key=True,
        verbose_name="Identifiant station",
    )
    nom = models.CharField(
        max_length=255,
        verbose_name="Nom de la station",
    )
    poste_ouvert = models.BooleanField(
        default=False,
        verbose_name="Poste ouvert",
    )
    type_poste = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Type de poste",
    )
    lon = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Longitude",
    )
    lat = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Latitude",
    )
    alt = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Altitude (m)",
    )
    poste_public = models.BooleanField(
        default=False,
        verbose_name="Poste public",
    )
    departement = models.CharField(
        max_length=10,
        default="17",
        verbose_name="Département",
    )
    date_mise_a_jour = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour",
    )

    class Meta:
        verbose_name = "Station météo"
        verbose_name_plural = "Stations météo"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.id_station})"
