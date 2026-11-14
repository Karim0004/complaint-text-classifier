import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

# every model takes the cleaned text column as X, so they all go through cross_validate() the same way


def majority():
    return DummyClassifier(strategy="most_frequent")


def log_word_count(text):
    """Log of the number of words in each narrative, as a single column."""
    words = text.str.split().str.len().to_numpy(dtype=float)
    return np.log1p(words).reshape(-1, 1)


def length_only():
    """Logistic regression that only knows how long the narrative is."""
    return make_pipeline(FunctionTransformer(log_word_count), StandardScaler(),
                         LogisticRegression(class_weight="balanced"))


def tfidf_logistic():
    """TF-IDF on single words, then logistic regression with balanced class weights.

    English stop words are dropped, and so are words in fewer than 5 narratives. The vectorizer is
    part of the pipeline, so in cross-validation it's fitted on the training folds only.
    """
    vectorizer = TfidfVectorizer(stop_words="english", min_df=5)
    return make_pipeline(vectorizer, LogisticRegression(class_weight="balanced", max_iter=1000))


def cross_validate(model, X, y, groups=None, n_splits=5, seed=0):
    """Stratified k-fold on the training set.

    With groups, rows from the same group always land in the same fold. Returns the out-of-fold
    probabilities and a table with ROC-AUC and average precision for each fold.
    """
    if groups is None:
        folds = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    else:
        folds = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    oof = np.zeros(len(y))
    scores = []
    for train_idx, val_idx in folds.split(X, y, groups):
        fitted = clone(model).fit(X.iloc[train_idx], y.iloc[train_idx])
        oof[val_idx] = fitted.predict_proba(X.iloc[val_idx])[:, 1]
        scores.append({
            "roc_auc": roc_auc_score(y.iloc[val_idx], oof[val_idx]),
            "avg_precision": average_precision_score(y.iloc[val_idx], oof[val_idx]),
        })
    return oof, pd.DataFrame(scores)
