import json
import os
import zipfile
import hashlib
import urllib.request
import re
from datetime import datetime

ISSUE_BODY = os.environ["ISSUE_BODY"]
REPO = os.environ["GITHUB_REPOSITORY"]

def section(title):
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

def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

name = section("Clickpack name")
author = section("Author")
readme = section("Description / README")
has_noise = "Contains noise.wav" in ISSUE_BODY

# 🔥 FIND ATTACHED ZIP URL
match = re.search(r"https://github.com/.+/files/\d+/.+\.zip", ISSUE_BODY)
if not match:
    raise RuntimeError("No ZIP file uploaded to the issue")

zip_url = match.group(0)

slug = slugify(name)
out_dir = f"out/{slug}"
os.makedirs(out_dir, exist_ok=True)

zip_path = f"{out_dir}/clickpack.zip"

req = urllib.request.Request(
    zip_url,
    headers={"User-Agent": "ClickpackDB-Bot/1.0"}
)

with urllib.request.urlopen(req) as r, open(zip_path, "wb") as f:
    f.write(r.read())

size = os.path.getsize(zip_path)
with zipfile.ZipFile(zip_path) as z:
    uncompressed = sum(i.file_size for i in z.infolist())

checksum = md5(zip_path)

raw_url = f"https://raw.githubusercontent.com/{REPO}/main/{zip_path}"

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
    "url": raw_url,
    "checksum": checksum,
    "readme": readme or None,
    "version": db["version"]
}

with open("db.json", "w", encoding="utf-8") as f:
    json.dump(db, f, indent=2)

print("Clickpack uploaded & hosted:", raw_url)
