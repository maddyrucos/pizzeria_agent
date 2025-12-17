from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from pathlib import Path

from typing import List
import csv

class RAG:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.embeddings = SentenceTransformerEmbeddings(model_name=model_name)
        self._retriever = self._build_retriever()

    def _load_documents(self) -> List[Document]:
        """
        Собираем документы из CSV меню и отзывов, чтобы раздать их в Chroma.
        """
        root_dir = Path(__file__).resolve().parent.parent
        data_dir = root_dir / "data"

        documents: List[Document] = []

        menu_path = data_dir / "pizzeria_menu.csv"
        if menu_path.exists():
            with menu_path.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("name", "").strip()
                    category = row.get("category", "").strip()
                    description = row.get("description", "").strip()
                    price = row.get("price_usd", "").strip()

                    content = (
                        f"Menu item: {name} (category: {category}). "
                        f"Description: {description}. Price: ${price} USD."
                    )
                    documents.append(
                        Document(
                            page_content=content,
                            metadata={
                                "source": "menu",
                                "name": name,
                                "category": category,
                                "price": price,
                            },
                        )
                    )

        reviews_path = data_dir / "restaurant_reviews.csv"
        if reviews_path.exists():
            with reviews_path.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    title = row.get("Title", "").strip()
                    date = row.get("Date", "").strip()
                    rating = row.get("Rating", "").strip()
                    review_text = row.get("Review", "").strip()

                    content = (
                        f"Review titled '{title}' on {date} rated {rating}/5: {review_text}"
                    )
                    documents.append(
                        Document(
                            page_content=content,
                            metadata={
                                "source": "review",
                                "title": title,
                                "date": date,
                                "rating": rating,
                            },
                        )
                    )

        return documents


    def _build_retriever(self):
        persist_dir = Path(__file__).resolve().parent.parent / "data" / "chroma_db"

        if persist_dir.exists() and any(persist_dir.iterdir()):
            vectorstore = Chroma(
                collection_name="pizzeria-knowledge",
                persist_directory=str(persist_dir),
                embedding_function=self.embeddings,
            )
        else:
            vectorstore = Chroma.from_documents(
                self._load_documents(),
                embedding=self.embeddings,
                collection_name="pizzeria-knowledge",
                persist_directory=str(persist_dir),
            )
            vectorstore.persist()

        _retriever = vectorstore.as_retriever(search_kwargs={"k": 8})
        return _retriever