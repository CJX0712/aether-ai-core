"""评估层公开接口。"""

from .metrics import faithfulness, ndcg_at_k, recall_at_k
from .suite import run_suite

__all__ = ["run_suite", "recall_at_k", "ndcg_at_k", "faithfulness"]
