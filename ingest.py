"""Ingestion des PowerPoints dans ChromaDB"""


import os
from dotenv import load_dotenv
load_dotenv()


from langchain_community.document_loaders import UnstructuredPowerPointLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata


from config import FILES, PERSIST_DIR, COLLECTION_NAME, EMBED_MODEL




def main():
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(" OPENAI_API_KEY manquant dans .env")


    print(" Chargement des PowerPoints...\n")
   
    all_docs = []
    for path in FILES:
        if not os.path.isfile(path):
            print(f"⚠️  Fichier non trouvé: {path}")
            continue


        loader = UnstructuredPowerPointLoader(path, mode="paged", strategy="fast")
        docs = loader.load()


        for i, doc in enumerate(docs, start=1):
            doc.metadata["source"] = path
            doc.metadata["slide"] = i


        print(f"✓ {path}: {len(docs)} slides")
        all_docs.extend(docs)


    print(f"\n📄 Total: {len(all_docs)} documents")
   
    # Filtrage et embeddings
    all_docs = filter_complex_metadata(all_docs)
    embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
   
    # ChromaDB
    print(f"📥 Ajout à ChromaDB...")
    vectordb = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIR,
    )
    vectordb.add_documents(all_docs)
   
    print(f" Terminé! ({PERSIST_DIR})")




if __name__ == "__main__":
    main()

