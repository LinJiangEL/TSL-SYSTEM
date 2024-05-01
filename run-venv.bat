::YAwzoRdxOk+EWAjk
::fBw5plQjdCyDJGyX8VAjFJ+MmIJTw+N16zDSKtTf6vmMtkINaNUwaoTeyIiHI+8d+XnzfJcsw25lyJtcXEkWdxGkDg==
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF65
::cxAkpRVqdFKZSjk=
::cBs/ulQjdF65
::ZR41oxFsdFKZSDk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpSI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+IeA==
::cxY6rQJ7JhzQF1fEqQJhZksaHmQ=
::ZQ05rAF9IBncCkqN+0xwdVsFAlTMbgs=
::ZQ05rAF9IAHYFVzEqQIjKxZQAgGaOQs=
::eg0/rx1wNQPfEVWB+kM9LVsJDDeXLG6oJZg4pu3j6oo=
::fBEirQZwNQPfEVWB+kM9LVsJDDeXLG6oJZg4pu3j6oo=
::cRolqwZ3JBvQF1fEqQIRaBhZSESBM2WpCbkZqP/y++LHsVgNUfAycZzI07uAboA=
::dhA7uBVwLU+EWHyc5E4/Oh5GDCqHKHy1FL5cxOn5oYo=
::YQ03rBFzNR3SWATE0WwcZns=
::dhAmsQZ3MwfNWATE100gMQldSwyWfMlzVOVOuqjewcbJ4mwRWKItcYjTzqfOMuUA71fycJJjtg==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCyDJGyX8VAjFJ+MmIJTw+N16zDSKtTf6vmMtkINaPE8dYuV36yLQA==
::YB416Ek+ZW8=
::
::
::978f952a14a936cc963da21a135fa983
@echo off
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
goto UACPrompt
) else ( goto gotAdmin )
:UACPrompt
echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
"%temp%\getadmin.vbs"
exit /B
:gotAdmin
if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
pushd "%CD%"
CD /D "%~dp0"

cmd /K ".venv\Scripts\activate.bat"