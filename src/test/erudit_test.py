import requests
from bs4 import BeautifulSoup
import os
def get_erudit_xml_url(article_id):
    base_url = f"https://www.erudit.org/iderudit/{article_id}"
    response = requests.get(base_url)
    
    if response.status_code != 200:
        raise Exception(f"Erreur d'accès à la page pour {article_id}")
    
    soup = BeautifulSoup(response.text, 'html.parser')

    print("Tous les liens détectés sur la page :")
    for link in soup.find_all("a", href=True):
        print(" ➤", link["href"])

    xml_link = None
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.endswith(".xml") and article_id in href:
            xml_link = "https://www.erudit.org" + href
            break

    if not xml_link:
        raise Exception(f"Fichier XML introuvable pour {article_id}")
    
    return xml_link


def download_erudit_xml(article_id, output_dir="./"):
    # Lien XML direct basé sur l'article ID (tu l'as confirmé)
    xml_url = f"https://www.erudit.org/fr/revues/ciera/2023-n22-ciera08850/{article_id}.xml"
    
    response = requests.get(xml_url)
    if response.status_code == 200:
        # Crée le dossier de sortie s'il n'existe pas
        os.makedirs(output_dir, exist_ok=True)
        xml_path = os.path.join(output_dir, f"{article_id}.xml")
        with open(xml_path, "wb") as f:
            f.write(response.content)
        print(f"Fichier XML enregistré : {xml_path}")
    else:
        raise Exception(f"Échec du téléchargement depuis {xml_url} (code {response.status_code})")

# Exemple d’utilisation :
if __name__ == "__main__":
    article_id = "1107141ar"
    download_erudit_xml(article_id, output_dir="./xml_files")