# PowerShell script para criar atalho na área de trabalho
$WshShell = New-Object -ComObject WScript.Shell

# Encontrar Desktop (suporta OneDrive)
$DesktopPaths = @(
    "$env:USERPROFILE\OneDrive\Desktop",
    "$env:USERPROFILE\Desktop",
    [Environment]::GetFolderPath("Desktop")
)

$DesktopPath = $null
foreach ($path in $DesktopPaths) {
    if (Test-Path $path) {
        $DesktopPath = $path
        break
    }
}

if ($null -eq $DesktopPath) {
    Write-Host "Erro: Desktop não encontrado!"
    exit 1
}

# Criar atalho
$ShortcutPath = Join-Path $DesktopPath "Comp Kaggle Matemática.lnk"
$Link = $WshShell.CreateShortcut($ShortcutPath)
$Link.TargetPath = "D:\BIG DATA\BIG DATA\comp-kaggle-matematica\open-workspace.bat"
$Link.WorkingDirectory = "D:\BIG DATA\BIG DATA\comp-kaggle-matematica"
$Link.IconLocation = "C:\Program Files\Microsoft VS Code\Code.exe"
$Link.Description = "Abre VS Code com workspace da Competição Kaggle Matemática"
$Link.Save()

Write-Host "Atalho criado com sucesso em: $ShortcutPath"
