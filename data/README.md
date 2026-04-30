# Data Notes

This folder should contain only data that can be redistributed publicly.

Default rule: do not publish full raw CSV files from Reddit, news, or scraped source corpora. Publish only aggregate, derived, or sanitized files unless the team has explicitly confirmed that a file can be redistributed.

## Recommended Public Files

The public repository can include derived result files that do not expose restricted raw text at scale, such as:

- topic-word summaries
- topic-document probability summaries, if document text and sensitive identifiers are removed
- source-level topic distributions
- topic-level lexical JSD tables
- topic-level syntactic or relational JSD tables
- small illustrative examples used in the paper or public-facing materials

Recommended public CSV types:

- aggregate topic-level CSVs
- aggregate source-level CSVs
- JSD result CSVs
- figure source-data CSVs
- small example CSVs with minimal text and no sensitive identifiers

## Included Derived Files

The current repository uses the latest July 17, 2025 LLTR result group:

- `derived/topicDocProbabilities_8_topic_5_thetarole_sample_framing_news_2025-07-17.csv`
- `derived/topicWordFullDist_8_topic_5_thetarole_sample_framing_news_2025-07-17.csv`
- `derived/topicWordExamples_8_topic_5_thetarole_sample_framing_news_2025-07-17_public.csv`

The public document-probability file removes the unnamed pandas index column from the working file. The public examples file removes the long source-text column and keeps only the shorter example sentence field.

## Restricted or Review-Before-Public Files

Do not upload the full raw corpus unless licensing and platform constraints are checked. This includes:

- full Reddit comment/post text
- full news article text
- scraped linked news content
- large parsed corpora containing original sentences
- model intermediate files that contain recoverable raw text

This applies even when a file is technically "just a CSV." A CSV can still contain restricted raw text, usernames, source URLs, or recoverable document-level content.

## Suggested Data Layout

```text
data/
├── README.md
├── sample/
│   └── small_public_examples.csv
├── derived/
│   ├── topic_level_jsd.csv
│   ├── topic_word_framing_jsd.csv
│   └── topic_pair_source_pivot.csv
└── external/
    └── data_access_notes.md
```

## Data Access Statement

A suggested statement for the paper/repository:

> Due to platform terms and copyright restrictions, we do not redistribute all raw Reddit, news, or government communication data in this repository. We provide derived aggregate results, example materials, and code for reproducing the analysis where source data access is available.
