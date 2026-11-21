# Test NyaySaathi in Safari on your Mac

`127.0.0.1` always refers to the machine running the browser. The cloud server is not reachable from your Mac at that address; this chat currently has no working preview relay. This launcher instead starts the existing application on your own Mac.

1. Install [Homebrew](https://brew.sh) if it is not already installed.
2. Download and extract the source ZIP for `feature/generalized-consumer-analysis`.
3. Double-click **Run_NyaySaathi_Mac.command** in the extracted folder. It installs Python 3.12, Pango and Tesseract through Homebrew, creates a private project virtual environment, installs the pinned/hash-checked Python dependencies and starts the integrated app on loopback port 8011. Safari opens after `/api/health` passes. Keep Terminal open; Control-C stops the server.

You can also run the launcher from Terminal:

```bash
# Type bash followed by a space, drag Run_NyaySaathi_Mac.command into Terminal, then press Return.
bash /path/to/extracted/Run_NyaySaathi_Mac.command
```

The launcher works from paths containing spaces and does not change an existing `.venv` or read `.env` as shell code. It respects existing environment variables. If port 8011 is occupied, choose another port with `NYAYSAATHI_PORT=8012 bash /path/to/Run_NyaySaathi_Mac.command`.

Local preparation, evidence, documents/PDF and demo sharing can be tested without Gemini. **Cloud credentials are not included.** Live Gemini intake requires your own backend key and provider-terms acknowledgement configured on the Mac; see README.md and `.env.example`. Never paste a key into chat. Without them the app visibly uses local preparation and disables live AI. Optional Hindi OCR additionally requires Homebrew's `tesseract-lang` package.

Use fictional details only. No official legal passage has been admitted, so legal conclusions and statutory citations remain withheld. The source ZIP contains no runtime case database, demo password, cloud secret or approved law.

The launcher is syntax-checked and its non-macOS refusal is checked in the Linux cloud environment. An actual macOS/Homebrew/Safari run cannot be verified here. The existing application's Linux health, Gemini probes and browser rendering passed independently; that does not establish macOS execution.
