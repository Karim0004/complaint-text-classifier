import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler, TargetEncoder
from xgboost import XGBClassifier

# the features from the complaint-escalation project, without channel and consent,
# which are the same for every complaint that has a narrative
ONE_HOT = ["product", "sub_product", "company_response", "timely_response", "tags", "month", "weekday"]


def add_date_columns(df):
    df = df.copy()
    df["month"] = df["date_received"].dt.month.astype(str)
    df["weekday"] = df["date_received"].dt.day_of_week.astype(str)
    df["days_to_send"] = (df["date_sent"] - df["date_received"]).dt.days
    return df


def build_features(train, test):
    """Fit every encoder on train only and return the feature tables for train and test, with the same columns."""
    train, test = add_date_columns(train), add_date_columns(test)

    one_hot = OneHotEncoder(handle_unknown="ignore", sparse_output=False, dtype=np.uint8).fit(train[ONE_HOT])
    # the 30 most common issues get a column each and the rest share one "infrequent" column
    issue = OneHotEncoder(max_categories=31, handle_unknown="infrequent_if_exist", sparse_output=False,
                          dtype=np.uint8).fit(train[["issue"]])

    company_share = train["company"].value_counts(normalize=True)
    # cross-fitted on train, so a complaint's own label never goes into its company's value,
    # and companies that aren't in train get the train dispute rate
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    target = TargetEncoder(target_type="binary", smooth=50, cv=folds)
    company_rate_train = target.fit_transform(train[["company"]], train["disputed"])[:, 0]
    company_rate_test = target.transform(test[["company"]])[:, 0]

    def transform(df, company_rate):
        X = pd.concat([
            pd.DataFrame(one_hot.transform(df[ONE_HOT]), columns=one_hot.get_feature_names_out(), index=df.index),
            pd.DataFrame(issue.transform(df[["issue"]]), columns=issue.get_feature_names_out(), index=df.index),
        ], axis=1)
        X["company_share"] = df["company"].map(company_share).fillna(0).astype(float)
        X["company_rate"] = company_rate
        X["days_to_send"] = df["days_to_send"]
        return X

    return transform(train, company_rate_train), transform(test, company_rate_test)


def fields_logistic(company=True, text_score=False):
    """Logistic regression with balanced class weights on the table from build_features().

    The one-hot columns go in as they are and the numeric ones are scaled, with a log first for days_to_send
    since a few complaints took years. company=False is for a table with the two company columns dropped,
    and text_score=True for one with a text_score column added.
    """
    numeric = []
    if company:
        numeric += ["company_share", "company_rate"]
    if text_score:
        numeric += ["text_score"]
    scale = ColumnTransformer([
        ("days", make_pipeline(FunctionTransformer(np.log1p, feature_names_out="one-to-one"), StandardScaler()),
         ["days_to_send"]),
        ("numeric", StandardScaler(), numeric),
    ], remainder="passthrough", verbose_feature_names_out=False)
    return make_pipeline(scale, LogisticRegression(class_weight="balanced", max_iter=1000))


def fields_xgboost():
    """XGBoost with the settings chosen in the complaint-escalation project. Trees don't need the scaling."""
    return XGBClassifier(max_depth=6, learning_rate=0.1, n_estimators=300, tree_method="hist", n_jobs=-1,
                         random_state=0)
