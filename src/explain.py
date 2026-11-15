import numpy as np
import pandas as pd

# these all take a fitted TF-IDF + logistic regression pipeline, such as chosen() from src/models.py


def term_weights(model, X, y):
    """The model's weight for every word and phrase in its vocabulary.

    Next to each weight is the number of narratives in X that contain the term and their dispute rate.
    """
    vectorizer, classifier = model[0], model[-1]
    has_term = vectorizer.transform(X) > 0
    narratives = np.asarray(has_term.sum(axis=0)).ravel()
    disputed = np.asarray(has_term[(y == 1).to_numpy()].sum(axis=0)).ravel()
    return pd.DataFrame(
        {"weight": classifier.coef_[0], "narratives": narratives, "dispute_rate": disputed / narratives},
        index=vectorizer.get_feature_names_out(),
    )


def top_terms(weights, n=20):
    """The n terms with the largest weights towards a dispute and the n with the largest weights away from one."""
    ordered = weights.sort_values("weight", ascending=False)
    return pd.concat({"towards": ordered.head(n), "away": ordered.tail(n).iloc[::-1]})


def narrative_terms(model, text):
    """How much each term in one narrative moves its score: the term's TF-IDF value times its weight.

    Sorted from the biggest push towards a dispute to the biggest push away from one.
    """
    vectorizer, classifier = model[0], model[-1]
    row = vectorizer.transform([text])
    pushes = row.data * classifier.coef_[0][row.indices]
    return pd.Series(pushes, index=vectorizer.get_feature_names_out()[row.indices]).sort_values(ascending=False)
