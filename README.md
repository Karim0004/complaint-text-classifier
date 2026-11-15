# Complaint text classification

Does the text of a complaint say whether the consumer will dispute the company's response, and does it add anything to a model built on the complaint's other fields?

## Results

The text models, scored with 5-fold cross-validation on the training set (narratives received from Mar 2015 to Sep 2016), with narratives that share an opening kept in the same fold:

| Model | CV ROC-AUC | CV average precision |
| --- | ---: | ---: |
| Majority class | 0.500 | 0.232 |
| Length only | 0.567 | 0.276 |
| TF-IDF on words + logistic regression (baseline) | 0.629 | 0.343 |
| TF-IDF on words and two-word phrases + logistic regression (C 0.3), chosen | 0.650 | 0.364 |

The test set (37,405 narratives received from Oct 2016 to Feb 2017, 20.8% disputed) was used once, to compare the text with the fields from the complaint-escalation project on the same complaints:

| Model | Test ROC-AUC | Test average precision |
| --- | ---: | ---: |
| Fields (logistic regression) | 0.626 | 0.289 |
| Text (the chosen model above) | 0.642 | 0.319 |
| Fields and the text model's score (logistic regression) | 0.671 | 0.344 |

Adding the text score to the fields is worth 0.045 ROC-AUC, with a 95% interval of 0.040 to 0.051 from resampling the test set.
