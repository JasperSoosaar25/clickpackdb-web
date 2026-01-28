import json
import os
import re
import sys
import zipfile
import hashlib
import urllib.request
from datetime import datetime

ISSUE_BODY = os.environ["ISSUE_BODY"]
ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]

# --- helpers ---
def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def parse(label):
    m = re.search(rf"{label}\n(.+)", ISSUE_BODY)
    return m.group(1).strip() if m else ""

name = parse("Clickpack name")
author = parse("Author")
url = parse("Download URL")
has_noise = "Contains noise.wav" in ISSUE_BODY
readme = parse("Description / README")

print("Adding:", name)

os.makedirs("tmp", exist_ok=True)
zip_path = f"tmp/{ISSUE_NUMBER}.zip"

urllib.request.urlretrieve(url, zip_path)

size = os.path.getsize(zip_path)

with zipfile.ZipFile(zip_path) as z:
    uncompressed = sum(i.file_size for i in z.infolist())

checksum = md5(zip_path)

# --- load db ---
with open("db.json", "r", encoding="utf-8") as f:
    db = json.load(f)

db["updated_at_iso"] = datetime.utcnow().isoformat() + "Z"
db["updated_at_unix"] = int(datetime.utcnow().timestamp())

db["clickpacks"][name] = {
    "author": author,
    "size": size,
    "uncompressed_size": uncompressed,
    "has_noise": has_noise,
    "url": url,
    "checksum": checksum,
    "readme": readme or None,
    "version": db.get("version", 0) + 1
}

db["version"] = db.get("version", 0) + 1

with open("db.json", "w", encoding="utf-8") as f:
    json.dump(db, f, indent=2)

print("Done.")
