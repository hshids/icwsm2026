"""Final framing analysis utilities for the ICWSM 2026 COVID framing paper.

This script reproduces the main aggregate analyses from the cleaned July 17,
2025 LLTR output files:

- source-topic probability summaries
- lexical Jensen-Shannon divergence over topic-word distributions
- syntactic/relational Jensen-Shannon divergence over word-argument evidence
- heatmaps for lexical and syntactic divergence

Run from the repository root:

    python src/final_framing_analysis.py
"""

from __future__ import annotations

import argparse
import ast
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.spatial.distance import jensenshannon


SOURCES = ("gov", "news", "reddit")
SOURCE_PAIRS = (("gov", "news"), ("gov", "reddit"), ("news", "reddit"))
PAIR_COLUMNS = ("gov-news", "gov-reddit", "news-reddit")

DEFAULT_FULL_DIST = (
    Path("data")
    / "derived"
    / "topicWordFullDist_8_topic_5_thetarole_sample_framing_news_2025-07-17.csv"
)
DEFAULT_DOC_PROBS = (
    Path("data")
    / "derived"
    / "topicDocProbabilities_8_topic_5_thetarole_sample_framing_news_2025-07-17.csv"
)


def parse_pair_vector(value: object) -> dict[str, float]:
    """Parse the serialized relation-argument vector stored in the CSV."""
    if not isinstance(value, str) or not value.strip() or value.strip() == "nan":
        return {}
    try:
        parsed = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {str(k): float(v) for k, v in parsed.items()}


def js_divergence(p: np.ndarray, q: np.ndarray) -> float:
    """Return Jensen-Shannon divergence in [0, 1].

    scipy.spatial.distance.jensenshannon returns the square root of the
    divergence, so we square the distance to recover JS divergence.
    """
    return float(jensenshannon(p, q, base=2) ** 2)


def _source_pair_values(vecs: dict[str, np.ndarray]) -> dict[str, float]:
    return {
        "gov-news": js_divergence(vecs["gov"], vecs["news"]),
        "gov-reddit": js_divergence(vecs["gov"], vecs["reddit"]),
        "news-reddit": js_divergence(vecs["news"], vecs["reddit"]),
    }


def compute_relational_jsd(
    full_dist: pd.DataFrame,
    *,
    top_k: int | None = 100,
    eps: float = 1e-12,
) -> pd.DataFrame:
    """Compute LLTR syntactic/relational JSD for each topic and source pair."""
    df = full_dist.copy()
    if "pair2score" not in df.columns:
        df["pair2score"] = df["arg2_reln_vector"].apply(parse_pair_vector)

    rows: list[dict[str, float]] = []
    for topic_id, topic_df in df.groupby("topic_id"):
        pair_counter: defaultdict[str, float] = defaultdict(float)
        for pair_scores in topic_df["pair2score"]:
            for pair, score in pair_scores.items():
                pair_counter[pair] += float(score)

        if not pair_counter:
            row = {"topic": int(topic_id) + 1}
            row.update({col: np.nan for col in PAIR_COLUMNS})
            rows.append(row)
            continue

        sorted_pairs = sorted(pair_counter.items(), key=lambda item: item[1], reverse=True)
        selected_pairs = sorted_pairs if top_k is None else sorted_pairs[:top_k]
        vocab = [pair for pair, _ in selected_pairs]

        vecs: dict[str, np.ndarray] = {}
        for source in SOURCES:
            source_df = topic_df[topic_df["source"] == source]
            vec = np.zeros(len(vocab), dtype=float)
            for pair_scores in source_df["pair2score"]:
                vec += np.array([float(pair_scores.get(pair, 0.0)) for pair in vocab])

            total = vec.sum()
            if total == 0:
                vec = np.ones(len(vocab), dtype=float) / len(vocab)
            else:
                vec = (vec + eps) / (total + eps * len(vocab))
            vecs[source] = vec

        row = {"topic": int(topic_id) + 1}
        row.update(_source_pair_values(vecs))
        rows.append(row)

    return pd.DataFrame(rows).sort_values("topic").reset_index(drop=True)


def compute_lexical_jsd(
    full_dist: pd.DataFrame,
    *,
    topic_weight_col: str = "token_weight",
    count_col: str = "token_count",
    eps: float = 1e-12,
) -> pd.DataFrame:
    """Compute lexical JSD using topic weights reweighted by source usage."""
    rows: list[dict[str, float]] = []

    for topic_id, topic_df in full_dist.groupby("topic_id"):
        vocab = sorted(topic_df["word"].dropna().unique())
        topic_weights = (
            topic_df.groupby("word")[topic_weight_col]
            .first()
            .reindex(vocab)
            .fillna(0.0)
            .astype(float)
        )

        vecs: dict[str, np.ndarray] = {}
        for source in SOURCES:
            counts = (
                topic_df[topic_df["source"] == source]
                .groupby("word")[count_col]
                .sum()
                .reindex(vocab)
                .fillna(0.0)
                .astype(float)
            )
            vec = topic_weights.to_numpy() * counts.to_numpy()
            if vec.sum() == 0:
                vec = topic_weights.to_numpy().copy()
            vec = vec + eps
            vec = vec / vec.sum()
            vecs[source] = vec

        row = {"topic": int(topic_id) + 1}
        row.update(_source_pair_values(vecs))
        rows.append(row)

    return pd.DataFrame(rows).sort_values("topic").reset_index(drop=True)


def compute_source_topic_distribution(doc_probs: pd.DataFrame) -> pd.DataFrame:
    """Compute each source's normalized share within each topic."""
    pivot = doc_probs.pivot_table(
        values="probability_score",
        index="source",
        columns="topic_id",
        aggfunc="sum",
        fill_value=0.0,
    )
    normalized = pivot.div(pivot.sum(axis=0), axis=1)
    normalized.columns = [f"Topic {int(topic) + 1}" for topic in normalized.columns]
    return normalized.reset_index()


def pivot_jsd(jsd_df: pd.DataFrame) -> pd.DataFrame:
    return (
        jsd_df.melt(
            id_vars="topic",
            value_vars=list(PAIR_COLUMNS),
            var_name="source_pair",
            value_name="JSD",
        )
        .pivot(index="topic", columns="source_pair", values="JSD")
        .reindex(columns=list(PAIR_COLUMNS))
        .sort_index()
    )


def save_jsd_heatmap(jsd_df: pd.DataFrame, out_path: Path, *, title: str) -> None:
    pivot = pivot_jsd(jsd_df)
    fig, ax = plt.subplots(figsize=(7.2, 4.8), dpi=300)
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".2f",
        cmap="YlGnBu",
        vmin=0,
        vmax=1,
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "Jensen-Shannon Divergence"},
        ax=ax,
    )
    ax.set_title(title, pad=10)
    ax.set_xlabel("Source Pair")
    ax.set_ylabel("Topic")
    ax.set_yticklabels([f"Topic {int(topic)}" for topic in pivot.index], rotation=0)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def _write_table(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def run_analysis(
    *,
    full_dist_path: Path,
    doc_probs_path: Path,
    out_dir: Path,
    top_k_values: Iterable[int | None] = (50, 100, None),
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    full_dist = pd.read_csv(full_dist_path)
    doc_probs = pd.read_csv(doc_probs_path)

    lexical_jsd = compute_lexical_jsd(full_dist)
    _write_table(lexical_jsd, out_dir / "lexical_jsd.csv")
    save_jsd_heatmap(
        lexical_jsd,
        out_dir / "lexical_jsd_heatmap.png",
        title="Lexical Topic-Word JSD Across Sources",
    )

    for top_k in top_k_values:
        label = "all" if top_k is None else f"top{top_k}"
        relational_jsd = compute_relational_jsd(full_dist, top_k=top_k)
        _write_table(relational_jsd, out_dir / f"relational_jsd_{label}.csv")
        save_jsd_heatmap(
            relational_jsd,
            out_dir / f"relational_jsd_{label}_heatmap.png",
            title=f"LLTR Relational JSD Across Sources ({label})",
        )

    source_topic = compute_source_topic_distribution(doc_probs)
    _write_table(source_topic, out_dir / "source_topic_distribution.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-dist", type=Path, default=DEFAULT_FULL_DIST)
    parser.add_argument("--doc-probs", type=Path, default=DEFAULT_DOC_PROBS)
    parser.add_argument("--out-dir", type=Path, default=Path("results"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_analysis(
        full_dist_path=args.full_dist,
        doc_probs_path=args.doc_probs,
        out_dir=args.out_dir,
    )


if __name__ == "__main__":
    main()
