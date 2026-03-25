import sqlite3
import pandas as pd
import os

# Usar siempre la ruta absoluta a biblioteca.db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "biblioteca.db")


def cargar_desde_csv(csv_path="biblioteca_personal.csv"):
    """
    Importa los datos iniciales desde biblioteca_personal.csv y
    REEMPLAZA el contenido de la tabla 'libros'.

    Esta función SOLO debe usarse:
    - Automáticamente cuando la tabla está vacía (init_db)
    - O manualmente, de forma consciente, si quieres pisar todo.
    """
    if not os.path.exists(csv_path):
        return False

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_csv(csv_path)

    # Arreglar nombre de columna mal escrita si viene del CSV
    if "reseapersonal" in df.columns:
        df = df.rename(columns={"reseapersonal": "resenapersonal"})

    # Asegurar columnas necesarias
    for col in [
        "estado", "paginastotal", "paginasleidas", "fechainicio",
        "fechafin", "tiempolecturamin", "citafavorita",
        "etiquetas", "resenapersonal", "edicionespecial"
    ]:
        if col not in df.columns:
            if col in ["paginastotal", "paginasleidas", "tiempolecturamin", "edicionespecial"]:
                df[col] = 0
            else:
                df[col] = ""

    # Tipo correcto para edicionespecial
    if "edicionespecial" in df.columns:
        df["edicionespecial"] = df["edicionespecial"].astype(int)
    else:
        df["edicionespecial"] = 0

    # Estado por defecto
    df["estado"] = df["estado"].fillna("Leido")

    # IMPORTANTE: solo se usa cuando quieres pisar la tabla completa
    df.to_sql("libros", conn, if_exists="replace", index=False)
    conn.close()
    return True


def init_db():
    """
    Crea las tablas si no existen y, SOLO si la tabla 'libros'
    está vacía, importa el CSV inicial UNA VEZ.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS libros (
            id TEXT PRIMARY KEY,
            titulo TEXT NOT NULL,
            autor TEXT,
            saga TEXT,
            ordensaga TEXT,
            genero TEXT,
            editorial TEXT,
            formato TEXT,
            edicionespecial INTEGER DEFAULT 0,
            detallesedicion TEXT,
            imagenportadaurl TEXT,
            valoracionpersonal REAL,
            resenapersonal TEXT,
            estado TEXT DEFAULT 'Leido',
            paginastotal INTEGER DEFAULT 0,
            paginasleidas INTEGER DEFAULT 0,
            fechainicio TEXT,
            fechafin TEXT,
            tiempolecturamin INTEGER DEFAULT 0,
            citafavorita TEXT,
            etiquetas TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS diariolectura (
            id TEXT PRIMARY KEY,
            libroid TEXT NOT NULL,
            fecha TEXT NOT NULL,
            paginashoy INTEGER DEFAULT 0,
            nota TEXT,
            estadoanimo TEXT,
            FOREIGN KEY (libroid) REFERENCES libros(id)
        )
    """)

    # ¿Cuántos libros hay ahora mismo?
    try:
        c.execute("SELECT COUNT(*) FROM libros")
        n = c.fetchone()[0] or 0
    except Exception:
        n = 0

    conn.commit()
    conn.close()

    # Si la tabla está vacía, importamos una sola vez desde el CSV
    if n == 0:
        cargar_desde_csv("biblioteca_personal.csv")


def get_all_books():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM libros", conn)
    conn.close()
    return df


def get_book_by_id(book_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM libros WHERE id = ?", conn, params=(book_id,))
    conn.close()
    return df.iloc[0] if not df.empty else None


def add_book(book: dict):
    if "reseapersonal" in book:
        book["resenapersonal"] = book.pop("reseapersonal")

    conn = sqlite3.connect(DB_PATH)
    df = pd.DataFrame([book])
    df.to_sql("libros", conn, if_exists="append", index=False)
    conn.close()


def update_book(book_id, fields: dict):
    if "reseapersonal" in fields:
        fields["resenapersonal"] = fields.pop("reseapersonal")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    set_clause = ", ".join(f"{k}=?" for k in fields.keys())
    values = list(fields.values()) + [book_id]
    c.execute(f"UPDATE libros SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def delete_book(book_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM libros WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()


def add_entrada_diario(entrada: dict):
    conn = sqlite3.connect(DB_PATH)
    df = pd.DataFrame([entrada])
    df.to_sql("diariolectura", conn, if_exists="append", index=False)
    conn.close()


def get_diario_libro(libro_id):
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql(
            "SELECT * FROM diariolectura WHERE libroid = ? ORDER BY fecha DESC",
            conn,
            params=(libro_id,),
        )
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


def delete_entrada_diario(entrada_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM diariolectura WHERE id = ?", (entrada_id,))
    conn.commit()
    conn.close()


def get_all_diario():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql(
            """
            SELECT d.*, l.titulo, l.autor, l.imagenportadaurl
            FROM diariolectura d
            LEFT JOIN libros l ON d.libroid = l.id
            ORDER BY d.fecha DESC
            """,
            conn,
        )
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df