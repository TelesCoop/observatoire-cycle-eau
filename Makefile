include .env

BACK_CMD_BASE = cd back/ && pew in ${PEW_ENV}
BACK_CMD = ${BACK_CMD_BASE} python manage.py

# Département par défaut pour la liste des stations
DEPT        ?= 17


back_install:
	$(PIP) install -r back/requirements.txt

back_migrate:
	$(BACK_CMD) migrate

back_makemigrations:
	$(BACK_CMD) makemigrations observatoire

back_run:
	$(BACK_CMD) runserver


# =============================================================================
#  Données MétéoFrance
# =============================================================================

## Récupère la liste des stations d'un département (TOKEN obligatoire)
## Exemple : make fetch-stations TOKEN=eyJ... DEPT=17
.PHONY: fetch-stations
fetch-stations:
ifndef TOKEN
	$(error ❌  La variable TOKEN est obligatoire. Exemple : make fetch-stations TOKEN=eyJ...)
endif
	$(BACK_CMD) fetch_stations --token "$(TOKEN)" --departement "$(DEPT)"


## Récupère les données météo quotidiennes pour une station (TOKEN, STATION_ID et START obligatoires)
## Exemple : make fetch-meteo TOKEN=eyJ... STATION_ID=17300001 START=2023-01-01
## Exemple : make fetch-meteo TOKEN=eyJ... STATION_ID=17300001 START=2020-01-01 STOP=2024-12-31
.PHONY: fetch-meteo
fetch-meteo:
ifndef TOKEN
	$(error ❌  La variable TOKEN est obligatoire. Exemple : make fetch-meteo TOKEN=eyJ... STATION_ID=17300001 START=2023-01-01)
endif
ifndef STATION_ID
	$(error ❌  La variable STATION_ID est obligatoire. Lancez 'make fetch-stations TOKEN=...' pour obtenir la liste des stations.)
endif
ifndef START
	$(error ❌  La variable START est obligatoire (format : YYYY-MM-DD). Exemple : START=2023-01-01)
endif
ifdef STOP
	$(BACK_CMD) fetch_meteo_data --token "$(TOKEN)" --station-id "$(STATION_ID)" --start "$(START)" --stop "$(STOP)"
else
	$(BACK_CMD) fetch_meteo_data --token "$(TOKEN)" --station-id "$(STATION_ID)" --start "$(START)"
endif
