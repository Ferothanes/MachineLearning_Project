from backend.constants import VECTOR_DATABASE_PATH, DATA_PATH
import lancedb
from backend.data_models import Article
import time
from pathlib import Path


def setup_vector_db(path):
    Path(path).mkdir(exist_ok=True)
    vector_db = lancedb.connect(uri=path)
    vector_db.create_table("articles", schema=Article, exist_ok=True)

    return vector_db


def ingest_docs_to_vector_db(table):
    for file in DATA_PATH.glob("*.md"): #md
        with open(file, "r") as f:
            content = f.read()
        doc_id = file.stem 
        table.delete(f"doc_id = '{doc_id}'")
        table.add(
            [
                {
                    "doc_id": doc_id,
                    "filepath": str(file),   # full path to the file
                    "filename": file.stem,   # name without extension
                    "content": content,      # raw text that will be embedded
                }
            ]
        )

        print(table.to_pandas().shape)
        print(table.to_pandas()["filename"])
        time.sleep(5) # adjust this later depending on performance, 30sec takes long time to ingest


if __name__ == "__main__":
    vector_db = setup_vector_db(VECTOR_DATABASE_PATH)
    ingest_docs_to_vector_db(vector_db["articles"])
