#!/bin/bash
# Tonight, with nobody watching: the 01:00 test final with one stop on purpose in its middle (the desk must come back by itself), then the
# night's experiments (night.py), then nothing: no world and no process is left when it ends, about nine hours after the start.
#     bash tonight.sh          in tmux; read night_report.txt in the morning
cd "$(dirname "$0")" && source .venv/bin/activate
echo "$(date '+%H:%M:%S') tonight: the test final first" | tee -a tonight.log
(sleep "${1:-1500}"; pkill -INT -f "dispatch.py --final") &   # the stop on purpose, 25 minutes from now
timeout 3600 bash final.sh                                    # ends by itself with the test final; an hour at most if none is played
pkill -f "dispatch.py --final"; sleep 2
python check_final.py > final_check.txt 2>&1
python clean.py >> tonight.log 2>&1
echo "$(date '+%H:%M:%S') tonight: the experiments" | tee -a tonight.log
python night.py 4 "${2:-8}" 2>&1 | tee -a night.log
pkill -f "dispatch.py --final"
python clean.py >> tonight.log 2>&1
{ python sweep.py --summary tag=night; echo; python sweep.py --summary tag=dawn; echo; cat night_choice.json; echo; cat final_check.txt; echo; tail -40 final.log; } > night_report.txt 2>&1
echo "$(date '+%H:%M:%S') tonight: done, nothing is running. Read night_report.txt" | tee -a tonight.log
