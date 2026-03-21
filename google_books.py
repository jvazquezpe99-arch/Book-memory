import requests

GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"

def buscar_libros(query, max_results=8):
    params = {"q": query, "maxResults": max_results}
    try:
        r = requests.get(GOOGLE_BOOKS_API, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        results = []
        for item in data.get("items", []):
            info = item.get("volumeInfo", {})
            # Obtener la mejor imagen disponible
            img_links = info.get("imageLinks", {})
            img = img_links.get("thumbnail", img_links.get("smallThumbnail", ""))
            # Mejorar calidad imagen (zoom=1 -> zoom=0 da mayor res)
            if img:
                img = img.replace("zoom=1", "zoom=0").replace("http://", "https://")
            results.append({
                "titulo": info.get("title", "Sin título"),
                "autor": ", ".join(info.get("authors", ["Desconocido"])),
                "editorial": info.get("publisher", ""),
                "genero": ", ".join(info.get("categories", ["Sin categoría"])),
                "paginas_total": info.get("pageCount", 0),
                "imagen_portada_url": img,
                "descripcion": info.get("description", "Sin descripción disponible.")[:300],
                "isbn": next((i["identifier"] for i in info.get("industryIdentifiers", []) if "ISBN" in i["type"]), item.get("id","")),
                "anio": info.get("publishedDate", "")[:4],
            })
        return results
    except Exception as e:
        return []

def buscar_novedades(genero, max_results=6):
    # Mapeo de géneros en español a términos de búsqueda en inglés
    mapa_genero = {
        "Romantasy": "romantasy fantasy romance",
        "Fantasy": "fantasy magic",
        "Romance": "romance love story",
        "Young Adult": "young adult YA",
        "Dystopia": "dystopia dystopian",
        "Thriller": "thriller suspense",
        "Historical Fiction": "historical fiction",
        "Science Fiction": "science fiction",
        "Poetry": "poetry poems",
        "Non Fiction": "nonfiction",
        "Fantasía": "fantasy magic",
        "Thriller": "thriller suspense misterio",
        "Histórica": "novela historica",
    }
    termino = mapa_genero.get(genero, genero)
    query = f"subject:{termino}&orderBy=newest"
    return buscar_libros(query, max_results)

def buscar_por_autor(autor, max_results=6):
    query = f"inauthor:{autor}"
    return buscar_libros(query, max_results)
