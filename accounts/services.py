# level_test/services.py
import json
import os
import random
from typing import Any, Dict, List, Optional, Set, Tuple

DIFF_LEVELS = [1, 3, 5]
SELF_N = 2
KNOWLEDGE_N = 5

# 총점 -> 레벨 컷(임시값, 나중에 조정)
LEVEL_CUTS = [
    (0.0, 4.0, 1),
    (4.0, 7.0, 2),
    (7.0, 10.0, 3),
    (10.0, 13.0, 4),
    (13.0, 999.0, 5),
]

def load_bank() -> List[Dict[str, Any]]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "data", "bank.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def score_to_level(total: float) -> int:
    for lo, hi, lv in LEVEL_CUTS:
        if lo <= total < hi:
            return lv
    return 1

def pick_self_ids(bank: List[Dict[str, Any]], k: int = SELF_N) -> List[str]:
    self_qs = [q for q in bank if q["type"] == "self"]
    picked = random.sample(self_qs, k)
    return [q["id"] for q in picked]

def get_question_by_id(bank: List[Dict[str, Any]], qid: str) -> Dict[str, Any]:
    for q in bank:
        if q["id"] == qid:
            return q
    raise KeyError(f"question id not found: {qid}")

def update_difficulty_idx(current_idx: int, was_correct: bool) -> int:
    if was_correct:
        return min(current_idx + 1, len(DIFF_LEVELS) - 1)
    return max(current_idx - 1, 0)

def _pick_knowledge(bank: List[Dict[str, Any]], target_diff: int, asked: Set[str]) -> Optional[Dict[str, Any]]:
    pool = [q for q in bank if q["type"] == "knowledge" and q["difficulty"] == target_diff and q["id"] not in asked]
    if pool:
        return random.choice(pool)

    # fallback: 거리순
    diffs = sorted(DIFF_LEVELS, key=lambda d: (abs(d - target_diff), d))
    for d in diffs:
        pool2 = [q for q in bank if q["type"] == "knowledge" and q["difficulty"] == d and q["id"] not in asked]
        if pool2:
            return random.choice(pool2)
    return None

def next_question(bank: List[Dict[str, Any]], state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    state:
      phase: "self" | "knowledge" | "done"
      self_ids: [..] (길이 2)
      self_idx: int
      current_diff_idx: int (0~2)
      asked_ids: [..]
      knowledge_count: int (0~5)
    """
    phase = state["phase"]
    asked = set(state["asked_ids"])

    if phase == "self":
        qid = state["self_ids"][state["self_idx"]]
        q = get_question_by_id(bank, qid)
        return q

    if phase == "knowledge":
        if state["knowledge_count"] >= KNOWLEDGE_N:
            return None
        target_diff = DIFF_LEVELS[state["current_diff_idx"]]
        q = _pick_knowledge(bank, target_diff, asked)
        return q

    return None

def grade_and_advance(bank: List[Dict[str, Any]], state: Dict[str, Any], qid: str, picked_index: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    반환: (updated_state, result_payload)
    result_payload: 제출 직후 보여줄 정보(맞/틀, 획득점수 등)
    """
    q = get_question_by_id(bank, qid)
    options = q["options"]
    picked = options[picked_index]
    earned = float(picked["score"])

    payload = {
        "qid": qid,
        "earned": earned,
        "was_correct": None,
    }

    # 상태 업데이트
    state["asked_ids"].append(qid)

    if q["type"] == "self":
        state["total_self"] += earned
        state["self_idx"] += 1
        if state["self_idx"] >= len(state["self_ids"]):
            state["phase"] = "knowledge"
        return state, payload

    # knowledge
    was_correct = earned > 0
    payload["was_correct"] = was_correct
    state["total_knowledge"] += earned
    state["knowledge_count"] += 1
    state["current_diff_idx"] = update_difficulty_idx(state["current_diff_idx"], was_correct)

    if state["knowledge_count"] >= KNOWLEDGE_N:
        state["phase"] = "done"

    return state, payload
