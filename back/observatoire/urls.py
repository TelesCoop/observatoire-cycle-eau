from django.contrib import admin
from django.urls import path

from observatoire.views.donnees_meteo import DonneesMeteoListView
from observatoire.views.station_meteo import (
    StationMeteoDetailView,
    StationMeteoListView,
    StationMeteoOuvertesListView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # --- Stations météo ---
    # Liste toutes les stations (filtres optionnels : ?departement=17&poste_ouvert=true)
    path("api/stations/", StationMeteoListView.as_view(), name="station-list"),
    # Liste uniquement les stations ouvertes (posteOuvert=True)
    path(
        "api/stations/ouvertes/",
        StationMeteoOuvertesListView.as_view(),
        name="station-ouvertes-list",
    ),
    # Détail d'une station
    path(
        "api/stations/<str:id_station>/",
        StationMeteoDetailView.as_view(),
        name="station-detail",
    ),
    # --- Données météo quotidiennes ---
    # Données d'une station (filtres optionnels : ?date_debut=YYYY-MM-DD&date_fin=YYYY-MM-DD)
    path(
        "api/stations/<str:id_station>/donnees/",
        DonneesMeteoListView.as_view(),
        name="donnees-meteo-list",
    ),
]
