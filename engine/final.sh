#!/bin/bash
# Plays the final, and the test final, with the configuration in dispatch.py and model.json. If the process dies it starts again by itself:
# the desk then rebuilds its books from the world and from its journal (journal/<world>.jsonl), and goes on as the same desk.
#     tmux new -s final        then:   ./final.sh        (leave: Ctrl-b d      come back: tmux attach -t final)
# Extra --param name=value are passed on. To stop it for good: Ctrl-C twice within three seconds.
cd "$(dirname "$0")" && source .venv/bin/activate
set -a; [ -f .env ] && . ./.env; set +a   # the team key, also in a shell that has not loaded it yet
set -o pipefail
until python dispatch.py --final "$@" 2>&1 | tee -ia final.log; do
    echo "$(date '+%H:%M:%S') the desk stopped: starting again in 3 seconds" | tee -a final.log
    sleep 3
done
echo "$(date '+%H:%M:%S') the final is over" | tee -a final.log
