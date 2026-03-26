from rest_framework import serializers

from observatoire.models.station_meteo import StationMeteo


class StationMeteoSerializer(serializers.ModelSerializer):
    class Meta:
        model = StationMeteo
        fields = [
            "id_station",
            "nom",
            "poste_ouvert",
            "type_poste",
            "lon",
            "lat",
            "alt",
            "poste_public",
            "departement",
            "date_mise_a_jour",
        ]
