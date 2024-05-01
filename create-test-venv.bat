@echo off
rm -rf .test-venv
python3 -m venv .test-venv
@echo on
cmd /K ".test-venv\Scripts\activate"