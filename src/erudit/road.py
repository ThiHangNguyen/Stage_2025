# chemins_erudit :
# Dictionnaire qui mappe les champs cibles (title, authors, abstract, etc.)
# vers leurs expressions XPath dans les fichiers XML fournis par Érudit.
# Les valeurs None indiquent qu’il n’y a pas d’extraction directe prévue.

chemins_erudit = {
    "title": ".//er:grtitre/er:titre",
    "overline": ".//er:grtitre/er:surtitre | .//er:grtitre/surtitre | .//grtitre/er:surtitre | .//grtitre/surtitre",
    "subtitle": ".//er:grtitre/er:sstitre | .//er:grtitre/sstitre | .//grtitre/er:sstitre | .//grtitre/sstitre",
    "abstract": "//er:resume/er:alinea",
    "date": ".//er:date",
    "id": "//er:infoarticle/er:idpublic",
    "erudit_id": "@idproprio",
    "issn": ".//er:idissnnum",
    "language": "/er:article/@lang",
    "type": ".//er:type",
    "start_page": ".//er:pagination/er:ppage",
    "end_page": ".//er:pagination/er:dpage",
    "rights_text": "//er:droitsauteur/er:nomorg",
    "rights_link": "//er:droitsauteur/er:liensimple/@xlink:href",
    "keywords": None,
    "editorial_team": None, # traitement specifique 
    "issue_number": ".//er:numero/er:nonumero",
    "volume": ".//er:numero/er:volume",
    "volume_year": ".//er:pubnum/er:annee",
    "themes": ".//er:grtheme/er:theme",

    "annexes": ".//er:annexe",
    "acknowledgements": ".//er:merci/er:alinea",
    "biographical_notes": ".//er:grnotebio/er:notebio/er:alinea",
    "bibliographies": "//er:biblio/er:refbiblio",
    "notes": ".//er:note",
}
