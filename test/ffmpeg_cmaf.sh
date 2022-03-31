# Please write the input file name

ffmpeg \
-i xxx.mp4 \
-map 0 -c:a aac -c:v libx264 -b:v:0 1000k -s:v:0 1280x720 -profile:v:0 high \
-frag_duration 1000 -seg_duration 6 \
-adaptation_sets "id=0,streams=v id=1,streams=a" \
-dash_segment_type mp4 \
-streaming 1 \
-preset ultrafast \
-ldash 1 \
-live 1 \
-use_template 1 -use_timeline 0 \
-tune zerolatency \
-hls_playlist 1 \
-f dash \
-method PUT http://localhost:8000/content/manifest.mpd