# chemins_grobid :
# Dictionnaire qui mappe les champs cibles (title, authors, abstract, etc.)
# vers leurs expressions XPath dans les fichiers TEI produits par GROBID.
# Les valeurs None indiquent qu’il n’y a pas d’extraction directe prévue.

chemins_grobid = {
    "title": "//tei:titleStmt/tei:title",
    "overline" : None,
    "subtitle": "//tei:titleStmt/tei:title[@level='a' and @type='sub']",
    "authors": "//tei:sourceDesc//tei:author",

    "abstract": "//tei:profileDesc/tei:abstract//tei:p",
    "date": "//tei:sourceDesc//tei:date[@type='published']/@when",
    "id": "//tei:sourceDesc//tei:biblStruct/tei:idno[@type='DOI']",
    "erudit_id": None,
    "issn": "//tei:sourceDesc//tei:monogr/tei:idno[@type='ISSN']",
    "language": "//tei:teiHeader/@xml:lang",
    "type": "//tei:profileDesc/tei:textClass/tei:classCode",
    "start_page": "//tei:sourceDesc/tei:biblStruct/tei:monogr/tei:imprint/tei:biblScope[@unit='page']/@from",
    "end_page": "//tei:sourceDesc/tei:biblStruct/tei:monogr/tei:imprint/tei:biblScope[@unit='page']/@to",
    "rights_text": "//tei:publicationStmt/tei:availability/tei:licence",
    "rights_link": "//tei:publicationStmt/tei:availability/tei:licence/@target",
    "keywords": "//tei:profileDesc/tei:textClass/tei:keywords/tei:term",
    "issue_number": "//tei:sourceDesc//tei:biblStruct//tei:monogr//tei:imprint//tei:biblScope[@unit='issue']",
    "volume": "//tei:sourceDesc//tei:biblStruct//tei:monogr//tei:imprint//tei:biblScope[@unit='volume']",

    "annexes": "//tei:body//tei:div[contains(tei:head, 'Annexe')]",
    "acknowledgements": "//tei:div[@type='acknowledgement']",
    "biographical_notes": "//tei:back//tei:div[contains(tei:head, 'Note biographique')]",
    "bibliographies": ".//tei:back//tei:div[@type='references']//tei:listBibl//tei:biblStruct",
    "notes": "//tei:note",

}