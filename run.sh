
[ -d "env3" ] || {
    python -m venv --system-site-packages env3
    . env3/bin/activate && python -m pip install -r requirements.txt
}
. env3/bin/activate
python app.py $@
