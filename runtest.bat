pip install -U pip setuptools wheel
pip install -r "Temp\__prebuild__\win32\modlist.txt"
python system.py
rm -rf .test-venv