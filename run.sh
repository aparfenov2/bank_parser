
[ -d "env3" ] || {
    python3 -m venv env3
}
. env3/bin/activate
python3 -m pip install -r requirements.txt
python3 app.py
