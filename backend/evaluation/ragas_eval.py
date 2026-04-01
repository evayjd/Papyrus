from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_ollama import ChatOllama, OllamaEmbeddings
from datasets import Dataset
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models import Evaluation
from backend.core.config import settings
import uuid
from datetime import datetime, timezone


def get_ragas_llm():
    return LangchainLLMWrapper(ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    ))


def get_ragas_embeddings():
    return LangchainEmbeddingsWrapper(OllamaEmbeddings(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    ))


async def evaluate_report(
    db: AsyncSession,
    report_id: str,
    query: str,
    report_content: str,
    papers: list[dict],
) -> Evaluation | None:
    try:
        # 把论文摘要作为 context
        contexts = [
            f"{p.get('title', '')} {p.get('abstract', '')}"
            for p in papers
        ]

        dataset = Dataset.from_dict({
            "question": [query],
            "answer": [report_content],
            "contexts": [contexts],
            "ground_truth": [query],  # 用问题本身作为 ground truth
        })

        llm = get_ragas_llm()
        embeddings = get_ragas_embeddings()

        result = evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevancy, context_recall],
            llm=llm,
            embeddings=embeddings,
        )

        scores = result.to_pandas().iloc[0]

        evaluation = Evaluation(
            id=uuid.uuid4(),
            report_id=report_id,
            faithfulness=float(scores.get("faithfulness", 0)),
            answer_relevancy=float(scores.get("answer_relevancy", 0)),
            context_recall=float(scores.get("context_recall", 0)),
            created_at=datetime.now(timezone.utc),
        )
        db.add(evaluation)
        await db.flush()
        return evaluation

    except Exception as e:
        print(f"Ragas 评估失败: {e}")
        return None