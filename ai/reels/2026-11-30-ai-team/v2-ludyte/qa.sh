f=$1
ffprobe -v error -select_streams a -show_entries packet=pts_time -of csv=p=0 $f | awk -F, 'NR>1{d=$1-p; if(d>0.05) print "GAP",p,$1} {p=$1}'
echo vdur $(ffprobe -v error -select_streams v -show_entries stream=duration -of csv=p=0 $f) adur $(ffmpeg -nostdin -v error -y -i $f -vn /tmp/qa_a.wav && ffprobe -v error -show_entries format=duration -of csv=p=0 /tmp/qa_a.wav)
for r in "0 5" "5 12" "20 30" "38 41.5" "41.5 44.5"; do set -- $r; echo "$1-$2" $(ffmpeg -nostdin -ss $1 -to $2 -i $f -vn -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1); done
echo tail $(ffmpeg -nostdin -ss 43.6 -to 44.4 -i $f -vn -af volumedetect -f null - 2>&1 | grep mean_volume)
