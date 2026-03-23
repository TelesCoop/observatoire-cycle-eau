#!/bin/bash

[ $1 = '--help' ] && echo -e "Usage: $0 <BSS NUMBER>\nOutput: ./<BSS NUMBER>.zip" && exit 255

oldBSS=$1
BSS=$2
DATE=01/01/1980
QUAL=0
PIEZO=1

OUTPUT=$(echo $oldBSS | sed 's!/!-!').zip

echo $OUTPUT

JSON=$(curl --get \
  --data-urlencode "codeBss=$oldBSS" \
  --data-urlencode "dateDebExport=$DATE" \
  --data-urlencode "expPiezo=$PIEZO" \
  --data-urlencode "expQual=$QUAL" \
  "https://ades.eaufrance.fr/Export/ExportFichePtEau")

URL=$(echo $JSON | sed 's/\["\(.*\)",.*\]/\1/')

echo $JSON
echo $URL

curl --output $OUTPUT $URL

unzip $OUTPUT
rm $OUTPUT
sed 's/|/\t/g' -i ades_export/Descriptif/descriptif.txt
#BSS=`awk '{if (NR==2) print $1}' ades_export/Descriptif/descriptif.txt`
echo BSS $BSS
cp -r ades_export Data/Piezos/Raw/$BSS
rm -r ades_export
