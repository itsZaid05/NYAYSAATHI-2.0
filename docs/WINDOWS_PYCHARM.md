# Run locally in Windows PyCharm

These instructions start the existing app on the Windows PC running PyCharm. A cloud localhost address cannot be opened directly from another computer. Native Windows execution has not been verified in the Linux test environment.

## Install native prerequisites

In Windows PowerShell:

```powershell
winget install --exact --id Python.Python.3.12
winget install --exact --id MSYS2.MSYS2
```

Alternatively use the official Python 3.12 64-bit installer and MSYS2 installer. Keep MSYS2's default `C:\msys64` location. Restart PyCharm after installing Python.

Open the MSYS2 terminal and run:

```bash
pacman -Syu
```

If it asks you to close/reopen MSYS2, do so. Then:

```bash
pacman -S --needed mingw-w64-x86_64-pango
```

Accept the installation prompt. These PDF libraries are needed because the backend imports WeasyPrint.

## Prepare the project

Open the extracted repository in PyCharm. In its Terminal choose **PowerShell**, and use the folder containing `requirements.lock`:

```powershell
dir requirements.lock
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.lock
.\.venv\Scripts\python.exe -m pip install tzdata
New-Item -ItemType Directory -Force runtime\cache | Out-Null
$env:WEASYPRINT_DLL_DIRECTORIES = "C:\msys64\mingw64\bin"
$env:Path = "C:\msys64\mingw64\bin;$env:Path"
$env:XDG_CACHE_HOME = (Join-Path $PWD "runtime\cache")
.\.venv\Scripts\python.exe -c "from zoneinfo import ZoneInfo; from weasyprint import HTML; print('Dependencies OK:', ZoneInfo('Asia/Kolkata'))"
```

Windows needs `tzdata` for the application's IANA timezone lookup. It is an additional platform dependency absent from the original Linux lock. Native OCR requires a separately installed Tesseract executable on PATH; without it image extraction is visibly unavailable, while supported PDF/TXT preparation remains usable.

## Optional live Gemini configuration

Cloud credentials are not bundled. The backend does not automatically read `.env`. Set variables in the same terminal **before** starting the server; after provider terms/quota review:

```powershell
$secureKey = Read-Host "Enter your Gemini API key" -AsSecureString
$env:GEMINI_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password
Remove-Variable secureKey
$env:GEMINI_MODEL = "gemini-3.1-flash-lite"
$env:GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
$env:GEMINI_TERMS_REVIEWED = "true"
```

Do not put a real key in chat, frontend files, recordings or Git. Model availability is checked at runtime; this configuration is not a guarantee that another account has the same access. Without it, the app qualifies local preparation and disables live AI.

## Start and use the browser

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_demo
.\.venv\Scripts\python.exe -m scripts.run_demo --port 8011
```

Wait for `Uvicorn running on http://127.0.0.1:8011`, then open that URL in the browser **on this PC**. Keep the terminal running; Control-C stops it. These commands use PyCharm's terminal; a separate green-button Run configuration would need the same interpreter, working directory and environment variables.

If port 8011 is busy, use `--port 8012` and visit port 8012. Reapply the DLL/cache/key environment settings when opening a new terminal. Source/rights operator imports currently use a Unix file-locking implementation and were tested on Linux; these instructions do not claim Windows support for that separate offline-administration tool.

Use fictional details only. There are zero approved law passages, no officially filed complaint and no verified-advocate marketplace.
