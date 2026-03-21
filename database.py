import sqlite3
import pandas as pd
import os

DB_PATH = "biblioteca.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
CREATE TABLE IF NOT EXISTS libros (
    id TEXT PRIMARY KEY,
    titulo TEXT NOT NULL,
    autor TEXT,
    saga TEXT,
    orden_saga TEXT,
    genero TEXT,
    editorial TEXT,
    formato TEXT,
    edicion_especial INTEGER DEFAULT 0,
    detalles_edicion TEXT,
    imagen_portada_url TEXT,
    valoracion_personal REAL,
    resena_personal TEXT,
    estado TEXT DEFAULT 'Leído',
    paginas_total INTEGER DEFAULT 0,
    paginas_leidas INTEGER DEFAULT 0,
    fecha_inicio TEXT,
    fecha_fin TEXT,
    tiempo_lectura_min INTEGER DEFAULT 0,
    cita_favorita TEXT,
    etiquetas TEXT
)""")
    c.execute("""
CREATE TABLE IF NOT EXISTS diario_lectura (
    id TEXT PRIMARY KEY,
    libro_id TEXT NOT NULL,
    fecha TEXT NOT NULL,
    paginas_hoy INTEGER DEFAULT 0,
    nota TEXT,
    estado_animo TEXT,
    FOREIGN KEY (libro_id) REFERENCES libros(id)
)""")
    conn.commit()
    conn.close()

def cargar_desde_csv(csv_path="biblioteca_personal.csv"):
    if not os.path.exists(csv_path):
        return False
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_csv(csv_path)
    if "reseña_personal" in df.columns:
        df = df.rename(columns={"reseña_personal": "resena_personal"})
    for col in ["estado","paginas_total","paginas_leidas","fecha_inicio","fecha_fin",
                "tiempo_lectura_min","cita_favorita","etiquetas","resena_personal"]:
        if col not in df.columns:
            df[col] = "" if col not in ["paginas_total","paginas_leidas","tiempo_lectura_min"] else 0
    df["edicion_especial"] = df["edicion_especial"].astype(int) if "edicion_especial" in df.columns else 0
    df["estado"] = df["estado"].fillna("Leído")
    df.to_sql("libros", conn, if_exists="replace", index=False)
    conn.close()
    return True

def get_all_books():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM libros", conn)
    conn.close()
    return df

def update_book(book_id, fields: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if "reseña_personal" in fields:
        fields["resena_personal"] = fields.pop("reseña_personal")
    set_clause = ", ".join([f"{k}=?" for k in fields.keys()])
    values = list(fields.values()) + [book_id]
    c.execute(f"UPDATE libros SET {set_clause} WHERE id=?", values)
    conn.commit()
    conn.close()

def add_book(book: dict):
    if "reseña_personal" in book:
        book["resena_personal"] = book.pop("reseña_personal")
    conn = sqlite3.connect(DB_PATH)
    df = pd.DataFrame([book])
    df.to_sql("libros", conn, if_exists="append", index=False)
    conn.close()

def delete_book(book_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM libros WHERE id=?", (book_id,))
    conn.commit()
    conn.close()

def get_book_by_id(book_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM libros WHERE id=?", conn, params=(book_id,))
    conn.close()
    return df.iloc[0] if not df.empty else None

# ── Diario de lectura ─────────────────────────────────────────
def add_entrada_diario(entrada: dict):
    conn = sqlite3.connect(DB_PATH)
    df = pd.DataFrame([entrada])
    df.to_sql("diario_lectura", conn, if_exists="append", index=False)
    conn.close()

def get_diario_libro(libro_id):
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql(
            "SELECT * FROM diario_lectura WHERE libro_id=? ORDER BY fecha DESC",
            conn, params=(libro_id,))
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def delete_entrada_diario(entrada_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM diario_lectura WHERE id=?", (entrada_id,))
    conn.commit()
    conn.close()

def get_all_diario():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql(
            """SELECT d.*, l.titulo, l.autor, l.imagen_portada_url
               FROM diario_lectura d
               LEFT JOIN libros l ON d.libro_id = l.id
               ORDER BY d.fecha DESC""", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df
