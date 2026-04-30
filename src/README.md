# Source Code

Place reusable Python code here.

Recommended modules:

- `preprocessing.py`
- `topic_modeling.py`
- `lltr_framing.py`
- `jsd.py`
- `plotting.py`
- `final_framing_analysis.py`

The current working directory contains useful analysis scripts, but the public repository should avoid publishing exploratory notebooks as the only reproducibility path. Moving core logic into scripts will make the repo easier for reviewers and future readers to use.

The current cleaned entry point is `final_framing_analysis.py`, which computes the aggregate topic-level and source-level results from the July 17, 2025 derived CSV files.
