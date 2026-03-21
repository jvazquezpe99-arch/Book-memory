import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def recomendar_libros(df, n=6):
    """
    Sistema de recomendación basado en similitud de contenido.
    Usa géneros, autores y sagas de los libros mejor valorados.
    """
    leidos = df[df["estado"] == "Leído"].copy()
    if leidos.empty:
        return pd.DataFrame()

    leidos["valoracion_personal"] = pd.to_numeric(leidos["valoracion_personal"], errors="coerce").fillna(3)
    top_libros = leidos[leidos["valoracion_personal"] >= 4]
    if top_libros.empty:
        top_libros = leidos

    # Crear perfil de gustos
    top_libros["features"] = (
        top_libros["genero"].fillna("") + " " +
        top_libros["autor"].fillna("") + " " +
        top_libros["saga"].fillna("")
    )

    # Todos los libros con features
    df["features"] = (
        df["genero"].fillna("") + " " +
        df["autor"].fillna("") + " " +
        df["saga"].fillna("")
    )

    tfidf = TfidfVectorizer()
    perfil_texto = " ".join(top_libros["features"].tolist())

    try:
        matriz = tfidf.fit_transform(df["features"].tolist() + [perfil_texto])
        perfil_vec = matriz[-1]
        libros_vec = matriz[:-1]
        similitudes = cosine_similarity(perfil_vec, libros_vec).flatten()
        df = df.copy()
        df["similitud"] = similitudes

        # Excluir ya leídos
        ids_leidos = leidos["id"].tolist()
        candidatos = df[~df["id"].isin(ids_leidos)].copy()
        candidatos = candidatos.sort_values("similitud", ascending=False)
        return candidatos.head(n)
    except:
        return pd.DataFrame()

def libros_pendientes_saga(df):
    """Detecta sagas incompletas: libros en biblioteca sin leer."""
    leidos_ids = df[df["estado"] == "Leído"]["id"].tolist()
    pendientes = df[(df["saga"] != "") & (~df["id"].isin(leidos_ids)) & (df["estado"] != "Leído")]
    return pendientes.sort_values(["saga", "orden_saga"])
