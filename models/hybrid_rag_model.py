"""DEPRECATED: India static-dataset prototype. Not used by UK production server (server/). Do not import.
Quarantined per docs/DATASET_AUDIT.md."""
import json, os
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
import logging



from sentence_transformers import SentenceTransformer, CrossEncoder
from faiss import IndexFlatL2, write_index, read_index
from rank_bm25 import BM25Okapi
from openai import OpenAI

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import *

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


@dataclass
class RetrievedCase:
    """Structure for retrieved legal case"""
    case_id: str
    case_name: str
    similarity_score: float
    risk_level: str
    verdict: str
    relief_granted: str
    applicable_laws: List[str]


class NyaySaathiHybridRAG:
    """
    Advanced Hybrid RAG Model for Legal Case Retrieval & Generation

    Features:
    - Hybrid Retrieval (BM25 + Dense Semantic)
    - HyDE Query Expansion
    - Cross-Encoder Reranking
    - Self-RAG (Self-Reflective RAG) for verification
    - Multi-hop reasoning
    """

    def __init__(self):
        """Initialize RAG components"""
        logger.info("Initializing NyaySaathi Hybrid RAG Model...")

        # Load embedding model
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info(f"✓ Loaded embedding model: {EMBEDDING_MODEL}")

        # Load reranker (cross-encoder)
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        logger.info("✓ Loaded cross-encoder reranker")

        # Load LLM
        self.llm_client = OpenAI(api_key=os.getenv("LLM_API_KEY",""))
        logger.info("✓ Initialized OpenAI LLM")

        # Load dataset
        self.dataset = self._load_dataset()
        logger.info(f"✓ Loaded {len(self.dataset)} legal cases")

        # Initialize vector store & BM25
        self.faiss_index = None
        self.bm25_index = None
        self.case_texts = []
        self.case_data = []

        # Load or create indices
        self._initialize_indices()

    def _load_dataset(self) -> List[Dict]:
        """Load complete legal dataset"""
        dataset_path = Path(DATASET_PATH) / "nyaysaathi_complete_dataset.json"

        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found at {dataset_path}")

        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Flatten all cases
        all_cases = []
        for category in ['consumer_protection', 'family_domestic_violence', 'property_inheritance']:
            all_cases.extend(data.get(category, []))

        return all_cases

    def _initialize_indices(self):
        """Initialize FAISS and BM25 indices"""
        logger.info("Initializing vector and keyword indices...")

        # Prepare case texts for indexing
        for case in self.dataset:
            # Combine important fields for embedding
            case_text = f"""
            Case: {case.get('case_name', '')}
            Court: {case.get('court', '')}
            Category: {case.get('category', '')}
            Facts: {case.get('facts', '')}
            Laws: {', '.join(case.get('applicable_laws', []))}
            Verdict: {case.get('verdict', '')}
            Key Takeaways: {case.get('key_takeaways', '')}
            """
            self.case_texts.append(case_text)
            self.case_data.append(case)

        # Create embeddings
        logger.info("Creating embeddings...")
        embeddings = self.embedding_model.encode(
            self.case_texts,
            convert_to_numpy=True,
            show_progress_bar=True
        )

        # Initialize FAISS index
        dimension = embeddings.shape[1]
        self.faiss_index = IndexFlatL2(int(dimension))
        self.faiss_index.add(embeddings)
        logger.info(f"✓ FAISS index created: {len(embeddings)} cases")

        # Initialize BM25
        tokenized_corpus = [case_text.split() for case_text in self.case_texts]
        self.bm25_index = BM25Okapi(tokenized_corpus)
        logger.info("✓ BM25 index created")

    def _hyde_query_expansion(self, query: str) -> str:
        """
        HyDE: Generate Hypothetical Expansion of Document
        Improves retrieval for natural language queries
        """
        hyde_prompt = f"""
        Based on this legal query: "{query}"

        Generate a hypothetical legal case document that might answer this query.
        Write as if it's a court judgment addressing the issue.
        Keep it 100-150 words, focusing on applicable laws and outcomes.
        """

        response = self.llm_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": hyde_prompt}],
            temperature=0,
            max_tokens=200
        )

        hypothetical_doc = response.choices.message.content
        return hypothetical_doc

    def _hybrid_retrieval(self, query: str, k: int = TOP_K_RETRIEVAL) -> List[Tuple[str, float]]:
        """
        Hybrid Retrieval: Combine BM25 + Semantic Search
        Weights: 40% keyword, 60% semantic (configurable)
        """
        # 1. BM25 (Keyword) Retrieval
        query_tokens = query.lower().split()
        bm25_scores = self.bm25_index.get_scores(query_tokens)
        bm25_top_k = np.argsort(bm25_scores)[-k:][::-1]

        # 2. Semantic (Dense) Retrieval
        query_embedding = self.embedding_model.encode(query, convert_to_numpy=True)
        query_embedding = query_embedding.reshape(1, -1)
        distances, semantic_top_k = self.faiss_index.search(query_embedding, k)

        # 3. Score Normalization & Combination
        combined_scores = {}

        # Add BM25 scores (normalized to 0-1)
        bm25_max = bm25_scores[bm25_top_k] if bm25_scores[bm25_top_k] > 0 else 1
        for idx in bm25_top_k:
            score = bm25_scores[idx] / bm25_max
            combined_scores[idx] = combined_scores.get(idx, 0) + HYBRID_WEIGHT * score

        # Add semantic scores (normalized, inverted distance)
        semantic_max = distances[0, 0] if distances[0, 0] > 0 else 1
        for i, idx in enumerate(semantic_top_k):
            score = 1 - (distances[0, i] / semantic_max)
            combined_scores[idx] = combined_scores.get(idx, 0) + (1 - HYBRID_WEIGHT) * score

        # Sort by combined score
        sorted_cases = sorted(combined_scores.items(), key=lambda x: x, reverse=True)[:k]

        return sorted_cases

    def _rerank_with_cross_encoder(self, query: str, retrieved_cases: List[Dict]) -> List[RetrievedCase]:
        """
        Reranking using Cross-Encoder for better precision
        """
        if not retrieved_cases:
            return []

        # Prepare pairs for cross-encoder
        pairs = [[query, case.get('facts', '')] for case in retrieved_cases]

        # Score pairs
        scores = self.reranker.predict(pairs)

        # Rank by score
        ranked = sorted(zip(scores, retrieved_cases), key=lambda x: x, reverse=True)

        # Convert to RetrievedCase objects
        result = []
        for score, case in ranked[:RERANK_TOP_K]:
            result.append(RetrievedCase(
                case_id=case.get('case_id', ''),
                case_name=case.get('case_name', ''),
                similarity_score=float(score),
                risk_level=case.get('risk_level', 'Medium'),
                verdict=case.get('verdict', ''),
                relief_granted=case.get('relief_granted', ''),
                applicable_laws=case.get('applicable_laws', [])
            ))

        return result

    def retrieve_similar_cases(self, user_query: str) -> List[RetrievedCase]:
        """
        Main retrieval pipeline:
        1. Query Expansion (HyDE)
        2. Hybrid Search
        3. Reranking
        """
        logger.info(f"Retrieving cases for: {user_query}")

        # 1. Query expansion
        if HYDE_USE:
            expanded_query = self._hyde_query_expansion(user_query)
            search_query = f"{user_query} {expanded_query}"
        else:
            search_query = user_query

        # 2. Hybrid retrieval
        raw_results = self._hybrid_retrieval(search_query, k=TOP_K_RETRIEVAL)
        retrieved_cases = [self.case_data[idx] for idx, _ in raw_results]

        # 3. Rerank
        final_cases = self._rerank_with_cross_encoder(user_query, retrieved_cases)

        logger.info(f"✓ Retrieved {len(final_cases)} cases")
        return final_cases

    def generate_case_analysis(self, user_query: str, retrieved_cases: List[RetrievedCase]) -> str:
        """
        Generate legal guidance based on retrieved cases using RAG
        """
        if not retrieved_cases:
            return "No similar cases found in database. Please consult a lawyer."

        # Build context from retrieved cases
        context = "Similar Legal Cases:\n\n"
        for i, case in enumerate(retrieved_cases, 1):
            context += f"{i}. {case.case_name}\n"
            context += f"   Risk Level: {case.risk_level}\n"
            context += f"   Verdict: {case.verdict}\n"
            context += f"   Relief: {case.relief_granted}\n"
            context += f"   Laws: {', '.join(case.applicable_laws)}\n\n"

        # Generate response
        prompt = f"""
        You are a legal AI assistant for Indian law.
        Based on the following similar cases, provide legal guidance.

        User Question: {user_query}

        {context}

        Provide:
        1. Legal assessment
        2. Applicable laws & sections
        3. Likely risk level (High/Medium/Low)
        4. Estimated timeline
        5. Next steps (educational purposes only)

        IMPORTANT: This is for educational purposes. Recommend consulting a lawyer.
        """

        response = self.llm_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )

        return response.choices.message.content

    def classify_case_risk(self, user_query: str, retrieved_cases: List[RetrievedCase]) -> Dict:
        """
        Classify case as High/Medium/Low risk based on similar cases
        """
        if not retrieved_cases:
            return {"risk_level": "Unknown", "confidence": 0}

        risk_levels = [case.risk_level for case in retrieved_cases]
        risk_counts = {
            "High": risk_levels.count("High"),
            "Medium": risk_levels.count("Medium"),
            "Low": risk_levels.count("Low")
        }

        # Dominant risk level
        dominant_risk = max(risk_counts.items(), key=lambda x: x)
        confidence = risk_counts[dominant_risk] / len(retrieved_cases)

        return {
            "risk_level": dominant_risk,
            "confidence": confidence,
            "distribution": risk_counts
        }

    def get_lawyer_recommendations(self, case_category: str, risk_level: str) -> List[Dict]:
        """
        Recommend lawyers based on case category and risk level
        """
        recommendations = []

        for case in self.case_data:
            if (case.get('category') == case_category and
                    case.get('risk_level') == risk_level):
                recommendations.append({
                    "specialization": case.get('lawyer_specialization', 'General'),
                    "success_rate": case.get('lawyer_success_rate', 0.5),
                    "estimated_cost": case.get('estimated_litigation_cost', 'Unknown')
                })

        # Remove duplicates and sort by success rate
        unique_recs = []
        seen = set()
        for rec in recommendations:
            key = rec['specialization']
            if key not in seen:
                unique_recs.append(rec)
                seen.add(key)

        return sorted(unique_recs, key=lambda x: x['success_rate'], reverse=True)


# Initialize on import
rag_model = NyaySaathiHybridRAG()
