"""FAISS vector store for semantic search on financial documents."""
import logging
import os
import json
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, store_path: str = "data/vector_store", embedding_model: str = "text2vec-base-chinese"):
        self.store_path = store_path
        self.embedding_model = embedding_model
        self._index = None
        self._documents: List[Dict] = []
        self._embedder = None
        os.makedirs(store_path, exist_ok=True)

    def _get_embedder(self):
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer(self.embedding_model)
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")
                self._embedder = None
        return self._embedder

    def _get_index(self, dim: int = 768):
        if self._index is None:
            try:
                import faiss
                index_path = os.path.join(self.store_path, "index.faiss")
                if os.path.exists(index_path):
                    self._index = faiss.read_index(index_path)
                else:
                    self._index = faiss.IndexFlatL2(dim)
            except Exception as e:
                logger.warning(f"Failed to load FAISS index: {e}")
                self._index = None
        return self._index

    def add_documents(self, documents: List[Dict[str, str]]):
        """Add documents to the vector store.

        Each document should have 'text' and optional 'metadata' fields.
        """
        embedder = self._get_embedder()
        if embedder is None:
            logger.warning("Embedder not available, skipping document indexing")
            return

        texts = [doc["text"] for doc in documents]
        embeddings = embedder.encode(texts, show_progress_bar=False)

        index = self._get_index(embeddings.shape[1])
        if index is None:
            return

        import numpy as np
        index.add(np.array(embeddings, dtype=np.float32))
        self._documents.extend(documents)
        self._save()

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for similar documents."""
        embedder = self._get_embedder()
        index = self._get_index()
        if embedder is None or index is None or index.ntotal == 0:
            return []

        import numpy as np
        query_vec = embedder.encode([query], show_progress_bar=False)
        distances, indices = index.search(np.array(query_vec, dtype=np.float32), min(top_k, index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if 0 <= idx < len(self._documents):
                doc = self._documents[idx].copy()
                doc["score"] = float(1 / (1 + dist))
                results.append(doc)
        return results

    def _save(self):
        try:
            import faiss
            index_path = os.path.join(self.store_path, "index.faiss")
            if self._index is not None:
                faiss.write_index(self._index, index_path)
            docs_path = os.path.join(self.store_path, "documents.json")
            with open(docs_path, "w", encoding="utf-8") as f:
                json.dump(self._documents, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")

    def load(self):
        try:
            docs_path = os.path.join(self.store_path, "documents.json")
            if os.path.exists(docs_path):
                with open(docs_path, "r", encoding="utf-8") as f:
                    self._documents = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load vector store documents: {e}")

    @property
    def doc_count(self) -> int:
        return len(self._documents)
