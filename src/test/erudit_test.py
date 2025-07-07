import requests
import os

def get_redirected_url(article_id):
    """
    Suit la redirection depuis l'URL courte.
    """
    base_url = f"https://www.erudit.org/iderudit/{article_id}"
    response = requests.get(base_url, allow_redirects=True)
    if response.status_code != 200:
        raise Exception(f"Erreur d'accès à {base_url}")
    return response.url  

def download_erudit_xml(article_id, output_dir="./xml_files"):
    # Étape 1 : récupérer l’URL redirigée
    final_article_url = get_redirected_url(article_id)

    # Étape 2 : ajouter le suffixe .xml
    if final_article_url.endswith('/'):
        final_article_url = final_article_url[:-1]
    xml_url = final_article_url + ".xml"

    # Étape 3 : téléchargement
    response = requests.get(xml_url)
    if response.status_code == 200:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"{article_id}.xml")
        with open(path, "wb") as f:
            f.write(response.content)
        print(f"XML téléchargé : {path}")
    else:
        raise Exception(f"Échec de téléchargement depuis {xml_url} (code {response.status_code})")

if __name__ == "__main__":
    article_id = "1107141ar"
    download_erudit_xml(article_id)
