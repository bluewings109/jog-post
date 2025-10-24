#!/bin/sh

export PYTHONPATH=/app/src:${PYTHONPATH}

exec pdm run python -m org.onlypearson.jogpost.main
