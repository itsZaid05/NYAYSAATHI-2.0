"""Run the integrated application: python main.py"""

import os
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.app:app",
        host="127.0.0.1",
        port=int(os.getenv("PORT", "8011")),
        access_log=False,
    )
