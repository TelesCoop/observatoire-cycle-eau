from rest_framework import generics
from rest_framework.exceptions import NotFound

from observatoire.models.donnees_meteo import DonneesMeteo
from observatoire.models.station_meteo import StationMeteo
from observatoire.serializers.donnees_meteo import DonneesMeteoSerializer


class DonneesMeteoListView(generics.ListAPIView):
    """
    GET /api/stations/<id_station>/donnees/
    Retourne les données météo quotidiennes pour une station donnée.

    Paramètres de requête optionnels :
      - date_debut : filtre à partir d'une date (format YYYY-MM-DD)
      - date_fin   : filtre jusqu'à une date (format YYYY-MM-DD)
    """

    serializer_class = DonneesMeteoSerializer

    def get_queryset(self):
        station_id = self.kwargs.get("id_station")
        try:
            station = StationMeteo.objects.get(id_station=station_id)
        except StationMeteo.DoesNotExist:
            raise NotFound(
                detail=f"Station avec l'identifiant '{station_id}' introuvable."
            )

        qs = DonneesMeteo.objects.filter(station=station).order_by("date")

        date_debut = self.request.query_params.get("date_debut")
        date_fin = self.request.query_params.get("date_fin")

        if date_debut:
            qs = qs.filter(date__gte=date_debut)
        if date_fin:
            qs = qs.filter(date__lte=date_fin)

        return qs
