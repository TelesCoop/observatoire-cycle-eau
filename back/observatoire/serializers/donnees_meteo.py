from rest_framework import serializers

from observatoire.models.donnees_meteo import DonneesMeteo


class DonneesMeteoSerializer(serializers.ModelSerializer):
    station_nom = serializers.CharField(source="station.nom", read_only=True)

    class Meta:
        model = DonneesMeteo
        fields = [
            "id",
            "station",
            "station_nom",
            "date",
            "precipitation",
            "temperature_min",
            "temperature_max",
            "temperature_moyenne",
            "vent_moyen",
            "vent_rafale_max",
            "ensoleillement",
            "hauteur_neige",
            "donnees_brutes",
        ]
