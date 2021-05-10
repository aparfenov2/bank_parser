
[ -d "env3" ] || {
    python3 -m venv --system-site-packages env3
    python -m pip install -r requirements.txt
}
. env3/bin/activate
python app.py
