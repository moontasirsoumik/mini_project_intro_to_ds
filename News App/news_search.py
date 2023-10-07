import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

conn = sqlite3.connect("mini_project_ds.db")
cursor = conn.cursor()

df = pd.read_sql_query("SELECT content FROM news", conn)

conn.close()


def article_score(query, len):
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(df["content"])

    q = vectorizer.transform([query])

    sim = cosine_similarity(q, X)

    top_k = len
    indices = sim.argsort()[0][::-1][:top_k]

    return indices