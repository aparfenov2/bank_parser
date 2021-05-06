
[ -d "env3" ] || {
    python3 -m venv --system-site-packages env3
}
. env3/bin/activate
python -m pip install -r requirements.txt
python app.py
