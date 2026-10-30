
cd E:\Alphax\AlphaX_ZeroTech

python -m venv venv-local

.\venv\Scripts\python.exe -m pip install --upgrade pip

.\venv\Scripts\python.exe -m pip install -r requirements.txt

.\venv\Scripts\python.exe -m flask --app app run --debug
