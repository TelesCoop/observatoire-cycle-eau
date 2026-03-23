#!/bin/bash

STATIONID=$1
START=$2
STOP=$3
TOKEN=$4

[ -z "$1" ] && echo "Usage: $0 <STATIONID> <DATESTART> <DATESTOP> <TOKEN>" && exit 201
[ -z "$2" ] && echo "Usage: $0 <STATIONID> <DATESTART> <DATESTOP> <TOKEN>" && exit 202
[ -z "$3" ] && echo "Usage: $0 <STATIONID> <DATESTART> <DATESTOP> <TOKEN>" && exit 203
[ -z "$4" ] && echo "Usage: $0 <STATIONID> <DATESTART> <DATESTOP> <TOKEN>" && exit 204

[ $(date --date="$STOP" +%s) -gt $(date +%s) ] && STOP=$(date +%Y-%m-%d)

EPOCHSTART=$(date --date="$START" +%s)
EPOCHSTOP=$(date --date="$STOP" +%s)

LOCALSTART=$EPOCHSTART
while [ $EPOCHSTOP -gt $LOCALSTART ]
do
  LOCALSTOP=$EPOCHSTOP
  [ $LOCALSTOP -gt $(($LOCALSTART + 60 * 60 * 24 * 365 - 1)) ] && LOCALSTOP=$(($LOCALSTART + 60 * 60 * 24 * 365 - 1))

  JSON=$(curl "https://public-api.meteofrance.fr/public/DPClim/v1/commande-station/quotidienne?id-station=$STATIONID&date-deb-periode=$(date --date="@$LOCALSTART" +%Y-%m-%d)T00%3A00%3A00Z&date-fin-periode=$(date --date="@$LOCALSTOP" +%Y-%m-%d)T00%3A00%3A00Z" \
    -H 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0' \
    -H 'Accept: */*' -H 'Accept-Language: fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3' -H 'Accept-Encoding: gzip, deflate, br, zstd' \
    -H 'Referer: https://portail-api.meteofrance.fr/' \
    -H "Authorization: Bearer ${TOKEN}" \
    -H 'Origin: https://portail-api.meteofrance.fr' -H 'DNT: 1' -H 'Sec-GPC: 1' -H 'Connection: keep-alive' \
    -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: same-site' -H 'Priority: u=0' \
    -s)
  FILE=$(echo -n $JSON | sed 's/{"elaboreProduitAvecDemandeResponse": {"return": "\(.*\)"}}/\1/')

  [ $EPOCHSTART -eq $LOCALSTART ] && curl -s -X 'GET' \
    "https://public-api.meteofrance.fr/public/DPClim/v1/commande/fichier?id-cmde=${FILE}" \
    -H 'accept: */*' \
    -H "Authorization: Bearer ${TOKEN}" | sed 's/,/./g'
  [ ! $EPOCHSTART -eq $LOCALSTART ] && curl -s -X 'GET' \
    "https://public-api.meteofrance.fr/public/DPClim/v1/commande/fichier?id-cmde=${FILE}" \
    -H 'accept: */*' \
    -H "Authorization: Bearer ${TOKEN}" \
    | tail -n +2 | sed 's/,/./g'

  echo $(date --date="@$LOCALSTART" +%Y-%m-%d) 1>&2
  LOCALSTART=$(($LOCALSTOP + 1))
done


