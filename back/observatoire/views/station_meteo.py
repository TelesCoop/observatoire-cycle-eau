from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from observatoire.models.station_meteo import StationMeteo
from observatoire.serializers.station_meteo import StationMeteoSerializer


class StationMeteoListView(generics.ListAPIView):
    """
    GET /api/stations/
    Retourne toutes les stations météo stockées en base de données.

    Paramètres de requête optionnels :
      - departement : filtre par numéro de département (ex: ?departement=17)
      - poste_ouvert : filtre sur les postes ouverts (ex: ?poste_ouvert=true)
    """

    serializer_class = StationMeteoSerializer

    def get_queryset(self):
        qs = StationMeteo.objects.all()
        departement = self.request.query_params.get("departement")
        poste_ouvert = self.request.query_params.get("poste_ouvert")

        if departement:
            qs = qs.filter(departement=departement)

        if poste_ouvert is not None:
            if poste_ouvert.lower() in ("true", "1", "oui"):
                qs = qs.filter(poste_ouvert=True)
            elif poste_ouvert.lower() in ("false", "0", "non"):
                qs = qs.filter(poste_ouvert=False)

        return qs


class StationMeteoOuvertesListView(generics.ListAPIView):
    """
    GET /api/stations/ouvertes/
    Retourne uniquement les stations dont le poste est ouvert (posteOuvert=True).
    Ce sont ces stations qui sont utilisées pour récupérer les données météo.

    Paramètre de requête optionnel :
      - departement : filtre par numéro de département (ex: ?departement=17)
    """

    serializer_class = StationMeteoSerializer

    def get_queryset(self):
        qs = StationMeteo.objects.filter(poste_ouvert=True)
        departement = self.request.query_params.get("departement")
        if departement:
            qs = qs.filter(departement=departement)
        return qs


class StationMeteoDetailView(generics.RetrieveAPIView):
    """
    GET /api/stations/<id_station>/
    Retourne le détail d'une station météo.
    """

    serializer_class = StationMeteoSerializer
    queryset = StationMeteo.objects.all()
    lookup_field = "id_station"
