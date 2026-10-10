"""Owner-only invitation helper. Load review environment variables before running.

--open opens the invitation in a browser; --copy sends it to the Wayland
clipboard. The secret URL is never printed to standard output.
"""

import argparse
import os
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
action = parser.add_mutually_exclusive_group(required=True)
action.add_argument("--open", action="store_true")
action.add_argument("--copy", action="store_true")
args = parser.parse_args()
origin = os.environ.get("ARGAND_PUBLIC_ORIGIN", "")
token = os.environ.get("ARGAND_REVIEW_TOKEN", "")
expires = int(os.environ.get("ARGAND_REVIEW_EXPIRES", "0"))
if not origin.startswith("https://") or len(token) < 32 or expires <= time.time():
    raise SystemExit("Load an active review configuration first.")
url = origin.rstrip("/") + "/#invite=" + token
try:
    if args.copy:
        subprocess.run(
            ["wl-copy"],
            input=url.encode(),
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("Private invitation copied. Share only with your intended reviewers.")
    else:
        subprocess.run(
            ["xdg-open", url],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("Private review opened in the browser.")
except (OSError, subprocess.CalledProcessError):
    raise SystemExit("Could not open or copy the invitation on this desktop.") from None
