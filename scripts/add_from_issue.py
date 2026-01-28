import json
import os
import zipfile
import hashlib
import urllib.request
from datetime import datetime

ISSUE_BODY = os.environ["ISSUE_BODY"]
ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]

def section(title):
    """
    Extracts text under a markdown heading like:
    ### Title
    content
    """
    marker = f"### {title}"
    if marker not in ISSUE_BODY:
        return ""

    part = ISSUE_BODY.split(marker, 1)[1]
    lines = part.strip().splitlines()

    out = []
    for line in lines:
        if line.startswith("### "):
            break
        out.append(line)

    return "\n".join(out).strip().replace("_No response_", "").strip()

name = section("Clickpack name")
author = section("Author")
url = section("Download URL (zip)")
readme = section("Description / README")
has_noise = "Contains noise.wav" in ISSUE_BODY

if not url:
    raise RuntimeError("Download URL is empty — issue format invalid")

print("Adding:", name)

os.makedirs("tmp", exist_ok=True)
zip_path = f"tmp/{ISSUE_NUMBER}.zip"

urllib.request.urlretrieve(url, zip_path)

def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

size = os.path.getsize(zip_path)

with zipfile.ZipFile(zip_path) as z:
    uncompressed = sum(i.file_size for i in z.infolist())

checksum = md5(zip_path)

with open("db.json", "r", encoding="utf-8") as f:
    db = json.load(f)

now = datetime.utcnow()

db["updated_at_iso"] = now.isoformat() + "Z"
db["updated_at_unix"] = int(now.timestamp())
db["version"] = db.get("version", 0) + 1

db["clickpacks"][name] = {
    "author": author,
    "size": size,
    "uncompressed_size": uncompressed,
    "has_noise": has_noise,
    "url": url,
    "checksum": checksum,
    "readme": readme or None,
    "version": db["version"]
}

with open("db.json", "w", encoding="utf-8") as f:
    json.dump(db, f, indent=2)

print("Clickpack added successfully.")
