import requests
import os
import copy
from jinja2 import Environment, FileSystemLoader

SAVE_DIR = "images"
os.makedirs(SAVE_DIR, exist_ok=True)
Base_url = "https://mai.malofreeasacloud.fr/"
url_api = Base_url + "api/v2/tables/mknlasszm6dl5nn/records?offset=0&limit=25&where=&viewId=vw054q697uwdrw0a" 
headers = {"xc-token": os.getenv("XC_TOKEN")}
response = requests.get(url_api, headers=headers)
response = response.json()
list_items = response['list']

def download_image(url_path, counter):
    """Télécharge une image avec un nom img<num>.<ext>"""
    full_url = Base_url + url_path

    # Déduire l'extension depuis le chemin
    ext = url_path.split(".")[-1]
    filename = f"img{counter}.{ext}"

    print(f"Téléchargement : {full_url}")

    response = requests.get(full_url, headers=headers)

    if response.status_code == 200:
        filepath = os.path.join(SAVE_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"✔ Sauvegardé : {filepath}")
    else:
        print(f"❌ Erreur {response.status_code} pour {full_url}")
def downloads_images(list_items):
    counter = 1
    for item in list_items:
        images = item.get("image")

        if not images:
            continue

        for img in images:
            img_path = img.get("signedPath") or img.get("path")

            if img_path:
                download_image(img_path, counter)
                counter += 1

downloads_images(list_items)

def get_extension_from_mimetype(mimetype: str) -> str | None:
    """Retourne l'extension à utiliser à partir du mimetype."""
    if not mimetype:
        return None
    subtype = mimetype.split('/')[-1].lower()
    # Normalisations courantes
    mapping = {
        'jpeg': 'jpg',
        'jpg': 'jpg',
        'png': 'png',
        'webp': 'webp',
        'gif': 'gif',
        'svg+xml': 'svg'
    }
    return mapping.get(subtype, subtype)

# On ne modifie pas list_items : on travaille sur une copie pour préparer les données destinées au template
items_for_template = []
for idx, item in enumerate(list_items, start=1):
    # copie superficielle suffisante ici (on ne modifie pas les sous-objets originaux)
    item_copy = copy.deepcopy(item)

    local_image = None
    if item.get("image") and isinstance(item["image"], list) and len(item["image"]) > 0:
        mimetype = item["image"][0].get("mimetype")
        ext = get_extension_from_mimetype(mimetype)
        if ext:
            candidate = f"images/img{idx}.{ext}"
            # vérifie si le fichier local existe ; sinon on laisse None (ou on peut afficher un placeholder)
            if os.path.exists(candidate):
                local_image = candidate
            else:
                # si le fichier exact n'existe pas, on tente quelques alternatives courantes
                alt_candidates = [f"images/img{idx}.png", f"images/img{idx}.jpg", f"images/img{idx}.webp", f"images/img{idx}.gif"]
                for alt in alt_candidates:
                    if os.path.exists(alt):
                        local_image = alt
                        break
    # on ajoute le chemin local (ou None) sans toucher à list_items
    item_copy["local_image"] = local_image
    items_for_template.append(item_copy)

# Préparer Jinja2 et rendre le template
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('templates/page.html')

rendered = template.render(items=items_for_template)

with open('output.html', 'w', encoding='utf-8') as f:
    f.write(rendered)

print("output.html généré — ouvre-le dans ton navigateur")


