import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.svm import LinearSVC

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


def tfidf(ngram_range=(1, 1), stop_words="english", min_df=5):
    """TF-IDF vectorizer. The defaults are the baseline's: single words, English stop words dropped,
    and words in fewer than 5 narratives dropped."""
    return TfidfVectorizer(ngram_range=ngram_range, stop_words=stop_words, min_df=min_df)


def logistic(C=1.0):
    return LogisticRegression(C=C, class_weight="balanced", max_iter=1000)


def naive_bayes(alpha=1.0):
    return MultinomialNB(alpha=alpha)


def linear_svm(C=1.0):
    return LinearSVC(C=C, class_weight="balanced")


def tfidf_logistic(C=1.0, **tfidf_settings):
    """TF-IDF, then logistic regression with balanced class weights.

    The vectorizer is part of the pipeline, so in cross-validation it's fitted on the training folds only.
    """
    return make_pipeline(tfidf(**tfidf_settings), logistic(C))


def chosen():
    """The model picked in notebooks/06_models.ipynb: words and two-word phrases with the stop words left in."""
    return tfidf_logistic(C=0.3, ngram_range=(1, 2), stop_words=None)


def split_folds(X, y, groups=None, n_splits=5, seed=0):
    """Stratified folds. With groups, rows from the same group always land in the same fold."""
    if groups is None:
        folds = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    else:
        folds = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return folds.split(X, y, groups)


def fold_scores(y_true, scores):
    return {"roc_auc": roc_auc_score(y_true, scores), "avg_precision": average_precision_score(y_true, scores)}


def cross_validate(model, X, y, groups=None, n_splits=5, seed=0):
    """Stratified k-fold on the training set.

    Returns the out-of-fold probabilities and a table with ROC-AUC and average precision for each fold.
    """
    oof = np.zeros(len(y))
    scores = []
    for train_idx, val_idx in split_folds(X, y, groups, n_splits, seed):
        fitted = clone(model).fit(X.iloc[train_idx], y.iloc[train_idx])
        oof[val_idx] = fitted.predict_proba(X.iloc[val_idx])[:, 1]
        scores.append(fold_scores(y.iloc[val_idx], oof[val_idx]))
    return oof, pd.DataFrame(scores)


def vectorize_folds(vectorizer, X, y, groups=None, n_splits=5, seed=0):
    """Vectorize the text once per fold, on the same folds as cross_validate().

    Returns a list of (X_train, y_train, X_val, y_val) with the vectorizer fitted on the training part.
    Several classifiers can then be tried on one TF-IDF setting without vectorizing again.
    """
    folds = []
    for train_idx, val_idx in split_folds(X, y, groups, n_splits, seed):
        fitted = clone(vectorizer)
        X_tr = fitted.fit_transform(X.iloc[train_idx])
        folds.append((X_tr, y.iloc[train_idx], fitted.transform(X.iloc[val_idx]), y.iloc[val_idx]))
    return folds


def score_folds(classifier, folds):
    """Fit a classifier on each vectorized fold. Returns ROC-AUC and average precision for each fold."""
    scores = []
    for X_tr, y_tr, X_val, y_val in folds:
        fitted = clone(classifier).fit(X_tr, y_tr)
        # the SVM has no probabilities, and its decision values rank the narratives the same way
        if hasattr(fitted, "predict_proba"):
            scores.append(fold_scores(y_val, fitted.predict_proba(X_val)[:, 1]))
        else:
            scores.append(fold_scores(y_val, fitted.decision_function(X_val)))
    return pd.DataFrame(scores)
