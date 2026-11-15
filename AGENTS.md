# Repository Guidelines

## Project Structure

- `dispatch.py` is the entry point. `world.py` handles routing, hours, and model inputs. `notes_exactum.py` parses dealer notes. `model.json` holds fitted parameters, and `map.json` supports offline tools.
- `fit.py`, `sweep.py`, and `weeks.py` fit models and compare experiments. `replay_test.py` and `restart_test.py` are standalone checks. `dispatch_v1.py` through `dispatch_v3x.py` are historical versions.
- Start with `README.md` and `ARCHITECTURE_v1.md`. `NHAT_KY_THI_NGHIEM.md` records research, strategy changes, and results. `KE_HOACH_FINAL.md` covers final-day operations, and `PITCH_NOTES.md` holds presentation notes.

## Run and Develop Locally

Run commands from the directory containing `dispatch.py` and `map.json`. Use a Python virtual environment with the organizers’ `spread` kit, plus NumPy for model fitting. Set `SPREAD_URL` and `SPREAD_KEY` for service-backed runs. On PowerShell, `. .\load-env.ps1` loads them from a local `.env`.

- `python dispatch.py --level 8 --seed test-1` runs one practice week and saves it under `runs/`.
- `python sweep.py --seeds n-1:8 "tag=a" "tag=a,reserve=0"` compares two configurations on the same eight practice seeds.
- `python fit.py` fits `model.json` from saved practice weeks.
- `bash final.sh` runs the live final with automatic restart. Use practice commands for development.

## Code Style and Validation

Match the surrounding Python style. Use four spaces, `snake_case` for functions and variables, and `PascalCase` for classes. Preserve the conventions for cents and simulated minutes. The repo has no configured formatter, linter, or coverage target.

Pass an existing saved week to `python replay_test.py runs/<saved-week>.json.gz` and compare actions with the baseline on the same input. Use `python restart_test.py runs/<saved-week>.json.gz` in a disposable local copy because the script clears `journal/` before replaying. Keep credentials, saved runs, and journals out of commits.

## Local Changes and Git

The current reorganization is local and move-only. Keep code contents intact and move path-dependent engine files together. Use concise, descriptive commit subjects, following the existing `MathNet1 Spread desk: build frozen for the final` subject. Keep branches and commits local. Pushing to `buihin2007/Spread-Mathnet-` is prohibited, and pull requests are outside this workflow.
