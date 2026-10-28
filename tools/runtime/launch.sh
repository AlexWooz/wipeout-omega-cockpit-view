#!/usr/bin/env bash
# Start the game like the launcher does, through the peek gamemoderun.
S=$(cd "$(dirname "$0")" && pwd)
cd ~/Games/wipeout_pc
pkill -x gow3-probe; sleep 2; pkill -9 -x gow3-probe
: > out/pad; echo 0 > out/toggles; mkdir -p $S/rt; rm -f $S/rt/pid
PATH=$S:$PATH PEEK_DIR=$S/rt GOW3_GAMEMODE=1 GOW3_MANGOHUD=0 GOW3_GAME_DIR=$PWD/CUSA07671 GOW3_PATCHES='Native 4K rendering (no checkerboard);Cheat - VR ships outside VR' GOW3_PATCHES_ONLY=1 GOW3_LANGUAGE=1 GOW3_DISCORD=0 GOW3_STREAM_MEMORY=cached GOW3_GPU_ID=0 GOW3_EXPERIMENTAL_UPSCALER=0 GOW3_NEO=0 GOW3_MODS_ENABLED=1 GOW3_FSR4_DIR=$HOME/.local/share/wipeout-launcher/fsr4 GOW3_PAD_FILE=$PWD/out/pad GOW3_TOGGLE_FILE=$PWD/out/toggles setsid stdbuf -oL -eL bash run.sh > $S/rt/session.log 2>&1 < /dev/null &
for i in $(seq 1 120); do sleep 2; grep -q 'pad opened' $S/rt/session.log && break; grep -q 'exited' $S/rt/session.log && break; done
grep -E 'pad opened|exited|Traceback' $S/rt/session.log | head -3; cat $S/rt/pid 2>/dev/null
