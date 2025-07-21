import requests
import os
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO

def get_redirected_url(article_id):
    """
    Récupère l'URL finale (redirigée) d'un article Érudit à partir de son identifiant court.
    Exemple : "1065017ar" → URL complète avec DOI ou chemin final sur erudit.org.
    """
    base_url = f"https://www.erudit.org/iderudit/{article_id}"
    response = requests.get(base_url, allow_redirects=True)
    if response.status_code != 200:
        raise Exception(f"Erreur d'accès à {base_url}")
    return response.url  

def download_erudit_xml(article_id, output_dir=None):

    """
    Télécharge le fichier XML structuré d’un article Érudit à partir de son identifiant.
    Le fichier est sauvegardé dans le dossier output_dir.
    """
    if output_dir is None:
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/xml_erudit"))

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

def download_erudit_xml_2cols(pdfs_dir="data/pdfs/pdf_2cols", output_dir="data/raw/xml_erudit/xml_2cols"):
    """
    Télécharge les fichiers XML depuis Érudit pour chaque PDF dans le dossier pdfs_dir,
    et les enregistre dans output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(pdfs_dir):
        if not filename.endswith(".pdf"):
            continue
        article_id = filename.replace(".pdf", "")
        try:
            print(f"Téléchargement XML pour {article_id} (2 cols)...")
            download_erudit_xml(article_id, output_dir)
        except Exception as e:
            print(f"Erreur pour {article_id} : {e}")


def download_and_clean_erudit_pdf(article_id, output_dir=None):

    """
    Télécharge le PDF d’un article Érudit et supprime la première page (page de garde).
    Le fichier nettoyé est enregistré dans `output_dir`.
    """
    if output_dir is None:
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/pdfs"))

    os.makedirs(output_dir, exist_ok=True)

    # Étape 1 : récupérer l’URL du PDF
    final_article_url = get_redirected_url(article_id)
    if final_article_url.endswith('/'):
        final_article_url = final_article_url[:-1]
    pdf_url = final_article_url + ".pdf"

    # Étape 2 : télécharger en mémoire
    response = requests.get(pdf_url)
    if response.status_code != 200:
        raise Exception(f"Échec du téléchargement depuis {pdf_url} (code {response.status_code})")

    # Étape 3 : lire le PDF depuis les octets
    reader = PdfReader(BytesIO(response.content))
    writer = PdfWriter()

    if len(reader.pages) <= 1:
        print(f"Le fichier {article_id}.pdf n’a qu’une seule page.")
        return

    for i in range(1, len(reader.pages)):  # On saute la première page (i = 0)
        writer.add_page(reader.pages[i])

    # Étape 4 : sauvegarder le PDF nettoyé
    output_path = os.path.join(output_dir, f"{article_id}.pdf")
    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"PDF téléchargé et nettoyé (sans première page) : {output_path}")

def clean_pdf_2cols(pdfs_dir="data/pdfs/pdf_2cols"):

    """
    Nettoie les fichiers PDF dans le répertoire donné en supprimant la première page.
    Écrase les fichiers existants avec la version nettoyée.
    """
    for filename in os.listdir(pdfs_dir):
        if not filename.endswith(".pdf"):
            continue
        article_id = filename.replace(".pdf", "")
        try:
            print(f"Nettoyage du PDF {article_id} (2 colonnes)...")
            download_and_clean_erudit_pdf(article_id, output_dir=pdfs_dir)
        except Exception as e:
            print(f"Erreur lors du nettoyage de {article_id} : {e}")


def main():
    """
    Lit un fichier CSV contenant une liste d'identifiants d'articles,
    puis télécharge pour chacun le XML et le PDF nettoyé.
    """
    input_csv = "data/csv/article_ids_cqd27.csv"
    pdf_dir = "data/pdfs"
    os.makedirs(pdf_dir, exist_ok=True)

    ids = pd.read_csv(input_csv, header=None)[0].tolist()

    for article_id in ids:
        try:
            print(f"Téléchargement de {article_id}...")
            download_erudit_xml(article_id, None)
            download_and_clean_erudit_pdf(article_id, pdf_dir)
        except Exception as e:
            print(f"Erreur pour {article_id} : {e}")
    #download_erudit_xml_2cols()
    #clean_pdf_2cols()

if __name__ == "__main__":
    main()