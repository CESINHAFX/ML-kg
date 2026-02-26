@echo off
REM Abre VS Code com o workspace da Competicao Kaggle Matematica
REM Este arquivo eh chamado pelo atalho da area de trabalho

REM Tenta localizar VS Code
set "VS_CODE_PATH=C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe"
if not exist "%VS_CODE_PATH%" (
    set "VS_CODE_PATH=C:\Program Files\Microsoft VS Code\Code.exe"
)

REM Abre VS Code com o workspace
start "" "%VS_CODE_PATH%" "D:\BIG DATA\BIG DATA\comp-kaggle-matematica"

REM Encerra o script sem deixar o prompt visivel
exit
