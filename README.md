# Complaint text classification

Does the text of a complaint say whether the consumer will dispute the company's response, and does it add anything to a model built on the complaint's other fields?

## Results

Scored with 5-fold cross-validation on the training set (narratives received from Mar 2015 to Sep 2016), with narratives that share an opening kept in the same fold. The test set (Oct 2016 to Feb 2017) is only used once, at the end.

| Model | CV ROC-AUC | CV average precision |
| --- | ---: | ---: |
| Majority class | 0.500 | 0.232 |
| Length only | 0.567 | 0.276 |
| TF-IDF + logistic regression (balanced) | 0.629 | 0.343 |
