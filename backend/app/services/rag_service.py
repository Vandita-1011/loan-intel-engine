"""
rag_service.py
===============
RAG over data_dictionary.md + validation_rules.json using ChromaDB.
Provides grounded context retrieval for the LLM copilot.
"""

import json, logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_RAW = _ROOT / "data" / "raw"


class RAGService:
    """Retrieval-augmented generation service using ChromaDB."""

    def __init__(self):
        self.collection = None
        self.chunks: list[dict] = []
        self._loaded = False

    def load(self):
        """Load and index documents into ChromaDB."""
        logger.info("Initializing RAG service …")

        # ── Load documents ────────────────────────────────────────────
        docs = []

        dd_path = _RAW / "data_dictionary.md"
        if dd_path.exists():
            content = dd_path.read_text(encoding="utf-8")
            # Chunk by section
            sections = content.split("\n## ")
            for i, section in enumerate(sections):
                if section.strip():
                    chunk_text = ("## " + section) if i > 0 else section
                    docs.append({
                        "id": f"dd_{i}",
                        "text": chunk_text.strip(),
                        "source": "data_dictionary.md",
                        "section": chunk_text.split("\n")[0][:80],
                    })

        vr_path = _RAW / "validation_rules.json"
        if vr_path.exists():
            rules = json.loads(vr_path.read_text())
            for rule in rules.get("rules", []):
                text = f"Rule {rule['id']} ({rule['name']}): {rule['description']}. Condition: {rule['condition']}. Severity: {rule['severity']}."
                docs.append({
                    "id": rule["id"],
                    "text": text,
                    "source": "validation_rules.json",
                    "section": rule["name"],
                })

        self.chunks = docs

        if not docs:
            logger.warning("  No documents found for RAG")
            return

        # ── Index into ChromaDB ──────────────────────────────────────
        try:
            import chromadb
            client = chromadb.Client()

            # Delete if exists
            try:
                client.delete_collection("loan_docs")
            except Exception:
                pass

            self.collection = client.create_collection(
                name="loan_docs",
                metadata={"hnsw:space": "cosine"}
            )

            self.collection.add(
                ids=[d["id"] for d in docs],
                documents=[d["text"] for d in docs],
                metadatas=[{"source": d["source"], "section": d["section"]} for d in docs],
            )

            self._loaded = True
            logger.info(f"  ✓ Indexed {len(docs)} chunks into ChromaDB")

        except Exception as e:
            logger.warning(f"  ✗ ChromaDB init failed: {e}. Using fallback keyword search.")
            self._loaded = False

    def retrieve(self, query: str, n_results: int = 5) -> list[dict]:
        """Retrieve relevant chunks for a query."""
        if self.collection and self._loaded:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                )
                chunks = []
                for i, doc in enumerate(results["documents"][0]):
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    chunks.append({
                        "text": doc,
                        "source": meta.get("source", "unknown"),
                        "section": meta.get("section", ""),
                        "distance": results["distances"][0][i] if results["distances"] else 0,
                    })
                return chunks
            except Exception as e:
                logger.warning(f"ChromaDB query failed: {e}")

        # Fallback: keyword search
        query_lower = query.lower()
        scored = []
        for chunk in self.chunks:
            score = sum(1 for word in query_lower.split() if word in chunk["text"].lower())
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda x: -x[0])
        return [{"text": c["text"], "source": c["source"], "section": c["section"], "distance": 0}
                for _, c in scored[:n_results]]


# Singleton
rag_service = RAGService()
