from lxml import etree

def extract_from_path(root, xpath, namespaces=None):
    """
    Extrait le texte des noeuds XML correspondant à un XPath donné.
    Renvoie une liste de chaînes normalisées.
    """
    if namespaces is None:
        namespaces = {}

    elements = root.xpath(xpath, namespaces=namespaces)

    result = []
    for el in elements:
        if isinstance(el, etree._Element):
            text = "".join(el.itertext()).strip()
            if text:
                result.append(text)
        elif isinstance(el, str):
            result.append(el.strip())

    return result
