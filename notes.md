# Notes

## Initial exploration, 12 Nov 2026

Same file as the complaint-escalation project: 432,952 CFPB complaints received between 1 Jan 2015 and 24 Apr 2017. This project is about the narrative, the consumer's own description of what happened.

1. 164,437 complaints have a narrative (38%). The first is from 19 Mar 2015, and every one is a web complaint where the consumer agreed to publish it. Since that date 55% of web complaints have one, which is between 39% and 45% of all complaints each month from April 2015.
2. So a text model can only ever score part of the complaints. Complaints that came by phone, post, fax or referral never have a narrative, and neither do the 125,547 web complaints without consent.
3. Complaints with a narrative are disputed more often, 21.8% against 16.1% for the rest. The gap holds inside web complaints too, at 21.8% with consent against 17.5% without.
4. Debt collection (40,387), mortgage (32,858) and credit reporting (31,587) have the most narratives, the same top three as in the full data.
5. The median narrative is 136 words and 99% are under 3,900 characters. 1,183 are under 10 words ("this is not mine", "Debt has been paid"), which won't give a model much.
6. CFPB redacts personal details. 83% of narratives contain XXXX, about 9 times per narrative on average, dates come out like XXXX/XXXX/15, and 31% have an amount written as {$400.00}. Cleaning needs a rule for these, since XXXX would otherwise be one of the most common words.
7. 1,865 texts appear more than once (3,103 extra copies). The most repeated is a template letter sent to Experian 103 times, with TransUnion and Equifax versions behind it, and none of the 103 was disputed. Repeated texts are disputed less (16.1% against 22.0%), and copies of the same text could land on both sides of a train/test split.
8. Longer narratives are disputed more often, from 14.7% for up to 25 words to 29.5% over 400. A length-only model is worth having as a baseline.

## Cleaning, 12 Nov 2026

`load_text()` in src/data.py returns 149,661 complaints with a narrative, received from 19 Mar 2015 to 28 Feb 2017, with 15 columns and no missing values. The target is `disputed` (1 for Yes, 0 for No) and 22.6% of rows are 1.

1. Of the 164,437 complaints with a narrative, 434 have no dispute label and 14,342 came after 28 Feb 2017. The cut-off is the one from the complaint-escalation project, and the narrative rows show the same reason for it: the weekly dispute rate holds at about 19 to 23% until 12 Mar 2017 and ends at 1.6%.
2. `clean_text()` turns CFPB's redaction marks into three tokens. Amounts like {$400.00} become `xxmoney`, redacted dates like XX/XX/XXXX or XXXX/XXXX/15 become `xxdate`, and everything else becomes `xxxx`, with a run like XXXX XXXX XXXX counted once. That keeps the fact that a date, an amount or a name was there without leaving XXXX as the most common word. After cleaning 81% of narratives have `xxxx`, 31% `xxmoney` and 28% `xxdate`. The raw text stays in `narrative` and the cleaned one is `text`.
3. Lower-casing and punctuation are left for the vectorizer, so `text` still reads like the original.
4. Short narratives stay. None is empty after cleaning, 149 have under 5 words and 1,193 under 10. They're disputed far less often (9.4% under 5 words against 23.1% for 25 or more), and a model in use would get them too.
5. Repeated texts stay as well, with a `copies` column for how many complaints share the text. 4,753 complaints share theirs with at least one other (1,743 different texts). 78% of those texts went to more than one company, which is probably one consumer complaining about several companies at once, but there's no consumer ID to check. Texts with 10 or more copies are disputed only 7.6% of the time.
6. Copies could leak across a time split, so I checked: only 77 of the 37,405 complaints after 30 Sep 2016 repeat a text from before.
7. Channel and consent are dropped because every row is a web complaint with consent. The other fields from the first project are kept and cleaned the same way, for comparing the text with them later. That leaves 3,032 companies.

## EDA, 13 Nov 2026

The charts are in notebooks/03_eda.ipynb and reports/figures.

1. Mortgage narratives are the longest (median 205 words) and credit reporting the shortest (91). Disputed narratives are longer, 163 words against 129, and the dispute rate goes up with every length band, from 15.4% for 25 words or fewer to 30.6% for more than 400. That holds inside each of the four biggest products and is steepest for credit reporting (11.3% to 30.6%).
2. `xxxx` is in 81% of narratives, then credit (48%) and account (41%). The most common two-word phrases are credit report (18.8%) and credit card (10.8%).
3. `did` is in 33% of narratives and in 78% of those it's part of "did not". "not" is on the stop-word list, so the negation is lost when stop words are removed. The models should be tried with the stop words left in as well.
4. Legal and formal wording has the highest dispute rates: evidence 36.5%, alleged 36.3%, cfpb 34.8%, fdcpa 34.6%, certified mail 33.5%. Wording about phone calls and everyday banking has the lowest: `times day` 16.0% (mostly from calls "times a day"), late fee 18.5%, hung 18.6%, overdraft 18.7%.
5. Only 103 of the 1,006 words that are in at least 1% of narratives are below the overall rate of 22.6%. A long narrative contains more of the words and long narratives are disputed more, so part of a word's rate is length. The length-only baseline will show how much.
6. Company names carry the company's own rate. `equifax` is at 33.4% and `experian` at 18.3%, and complaints about the two companies are disputed 28.7% and 15.3% of the time. So some of what the text knows is which company the complaint is about, and that matters when the text is compared with the fields from the first project.
7. Besides the 4,753 exact copies, 9,828 narratives start with the same 100 characters as at least one other. 1,282 use an opening that appears 10 times or more, and they're disputed 13.3% of the time. Pairs are disputed about as often as one-off texts, 23.5% against 22.7%.
8. The same legal wording goes both ways. Narratives that mention the FCRA are disputed 34.6% of the time when the opening is used fewer than 10 times and 6.0% when it's one of the mass letters (350 narratives).

## Split, 13 Nov 2026

`time_split()` in src/data.py is the one from the complaint-escalation project, with the same dates, so both projects are tested on the same five months. Train is 19 Mar 2015 to 30 Sep 2016 and test is 1 Oct 2016 to 28 Feb 2017.

| Set | Rows | Share | Disputed | Dispute rate |
| --- | ---: | ---: | ---: | ---: |
| Train | 112,256 | 75.0% | 26,089 | 23.2% |
| Test | 37,405 | 25.0% | 7,795 | 20.8% |

1. The dispute rate drops from 23.2% in train to 20.8% in test, the same direction as in the first project (19.5% to 17.0%).
2. Student loans go from 4.4% of narratives to 12.3%, and mortgages from 21.5% to 17.6%. 277 companies (534 complaints) only appear in the test window.
3. Narrative length barely changes, with a median of 137 words in train and 133 in test.
4. 77 test narratives are exact copies of a training text, and 286 (0.8%) start with the same 100 characters as one. They're template letters and are disputed 14.3% of the time, against 20.9% for the rest of the test set.
5. Those 286 stay in the test set. A model in use would also get letters it has seen before, and they're too few to move the score much. The final test run will give the score without them as well.
6. Anything fitted on the text (the vocabulary, the TF-IDF weights, the model) only sees train.

## Baselines, 14 Nov 2026

The three models are in src/models.py and the scores are in notebooks/05_baselines.ipynb. Each model takes the cleaned text as its input and goes through `cross_validate()`, 5-fold stratified CV on train.

| Model | CV ROC-AUC | CV average precision |
| --- | ---: | ---: |
| Majority class | 0.500 | 0.232 |
| Length only (logistic regression on the log of the word count) | 0.567 | 0.276 |
| TF-IDF + logistic regression (balanced) | 0.629 | 0.343 |

1. The folds keep narratives with the same first 100 characters together. 7,236 of the 112,256 training narratives share an opening with another one, and with plain stratified folds a template letter's copies end up on both sides. For the TF-IDF model that's worth 0.005 ROC-AUC and 0.006 average precision (0.6335 and 0.3490 with plain folds). The length-only model scores the same either way, which points to the copies as the cause.
2. The majority model gets 0.500 and 0.232, the dispute rate in train.
3. Length alone gets 0.567 and 0.276. It's one number per narrative, the log of the word count.
4. TF-IDF with logistic regression gets 0.629 and 0.343, with the five folds between 0.624 and 0.634. It uses single words and drops English stop words and words in fewer than 5 narratives, which leaves 17,231 words when it's fitted on all of train. The vectorizer sits inside the pipeline, so each fold's vocabulary and weights come from its training folds only.
5. At a 0.5 cut-off the TF-IDF model flags 40.3% of narratives and catches 54.4% of the disputes (14,185 of 26,089), and 31.3% of the flagged ones are disputed. As in the first project, balanced weights make 0.5 a poor cut-off, and it's only here to give a feel for the scores.
6. The first project's logistic regression had a CV ROC-AUC of 0.646, but on all complaints. These scores are only on complaints with a narrative, so the two aren't comparable until both models are scored on the same rows.

Stop words stay out in this baseline. Leaving them in is the first thing to try in the next step, since the EDA showed that dropping them loses "not".

## Models, 15 Nov 2026

Everything is in notebooks/06_models.ipynb, on the grouped folds from the baselines. `vectorize_folds()` and `score_folds()` in src/models.py vectorize the text once per fold, so several classifiers can be tried on one TF-IDF setting without building it again.

TF-IDF settings, each with the baseline's logistic regression (C 1):

| TF-IDF setting | Features | CV ROC-AUC | CV average precision |
| --- | ---: | ---: | ---: |
| Words, stop words dropped (baseline) | 15,684 | 0.6285 | 0.3432 |
| Words | 15,992 | 0.6334 | 0.3472 |
| Words and two-word phrases | 243,473 | 0.6442 | 0.3652 |
| Words and two-word phrases, stop words dropped | 208,716 | 0.6397 | 0.3594 |
| Words and two-word phrases, min_df 2 | 563,822 | 0.6457 | 0.3664 |
| Words and two-word phrases, min_df 20 | 81,373 | 0.6405 | 0.3600 |

Classifiers on words and two-word phrases with the stop words left in:

| Classifier | CV ROC-AUC | CV average precision |
| --- | ---: | ---: |
| Logistic regression, C 0.1 | 0.6463 | 0.3538 |
| Logistic regression, C 0.3 | 0.6499 | 0.3640 |
| Logistic regression, C 1 | 0.6442 | 0.3652 |
| Logistic regression, C 3 | 0.6334 | 0.3560 |
| Naive Bayes, alpha 0.1 | 0.6284 | 0.3543 |
| Naive Bayes, alpha 0.3 | 0.6139 | 0.3431 |
| Naive Bayes, alpha 1 | 0.5569 | 0.2975 |
| Linear SVM, C 0.01 | 0.6447 | 0.3510 |
| Linear SVM, C 0.03 | 0.6503 | 0.3625 |
| Linear SVM, C 0.1 | 0.6463 | 0.3649 |
| Linear SVM, C 1 | 0.6162 | 0.3368 |

1. Leaving the stop words in is worth about 0.005 ROC-AUC, with single words and with phrases. That fits the EDA, where "did not" lost its "not".
2. Two-word phrases add 0.011 ROC-AUC and 0.018 average precision on top of that, with 15 times as many features.
3. The minimum document frequency matters little. Going down to 2 narratives more than doubles the features for 0.0015 ROC-AUC, and going up to 20 loses 0.004. It stays at 5.
4. Logistic regression at C 0.3 and the linear SVM at C 0.03 are level at 0.650, well inside the spread between folds (about 0.006). Both get worse as C goes up from there.
5. Naive Bayes is behind at every setting. With the default alpha of 1 it scores 0.557, below the length-only model, and alpha 0.1 brings it to 0.628. The likely reason is that it's fitted on TF-IDF weights, which are small, so a smoothing of 1 on each of 243,473 features swamps them.
6. The chosen model is logistic regression at C 0.3 on words and two-word phrases with the stop words left in, `chosen()` in src/models.py. The SVM is level with it but has no probabilities, which the decision step needs. Through the full pipeline it gets 0.650 ROC-AUC and 0.364 average precision, with the folds between 0.641 and 0.656, against 0.629 and 0.343 for the baseline.

The test set still hasn't been used. That happens once, in the text against fields step.

## Explain, 15 Nov 2026

The weights are in notebooks/07_explain.ipynb, with three helper functions in src/explain.py and a chart in reports/figures/term_weights.png. `chosen()` is fitted on all of train, and each of its 284,161 words and phrases gets a weight, positive towards a dispute and negative away from one.

| Direction | Ten largest weights |
| --- | --- |
| Towards a dispute | scottrade, equifax, tcpa, chase, attached, illegal, without, of, violated, cfpb |
| Away from a dispute | ve, payday, rushcard, experian, update, my bank, payday loan, error, rush, phone |

The same model fitted on one product at a time:

| Product | Towards a dispute | Away from a dispute |
| --- | --- | --- |
| Debt collection | tcpa, fcra, fdcpa, violation, verification, credit reports | calling my, times day, work, payday |
| Mortgage | fraud, false, statements, attached, note | help, to get, my home, sale, review |
| Credit reporting | equifax, inquiries, inquiry, authorization | experian, have never, never lived, owe |

1. Legal wording (illegal, violated, cfpb, fcra, tcpa) and `attached`, from consumers who sent documents, push towards a dispute. Payday loans, fees and phone calls push away. The EDA found the same groups in the raw dispute rates.
2. Company names have some of the largest weights in both directions. Two of them are events. Scottrade is in 151 narratives (80.1% disputed) and RushCard in 468 (3.8% disputed), and over 90% of each arrived between October and December 2015. Those two weights may not help in the test months. Equifax (about 3.0) and Experian (about -1.3) are the lasting ones, and they follow the two companies' own dispute rates in train, 28.9% and 15.7%.
3. Stop words have large weights too. `of`, `and`, `by` and `they` push towards a dispute and `my` and `had` push away. The most negative weight of all is `ve`, which is what's left of "I 've". My reading is that a narrative about what the company did scores higher than one that tells the consumer's own story.
4. A term's raw dispute rate and its weight can disagree. Five of the 20 most negative terms are in narratives that are disputed more often than the overall 23.2%. The raw rate includes length, and the weight is what the term adds once the rest of the narrative is counted.
5. In debt collection, wording about the law pushes towards a dispute and wording about phone calls pushes away: narratives with `times day` are disputed 12.7% of the time against 21.9% for the product. In mortgages it's accusations and paperwork against requests for help, with `fraud` narratives disputed 42.2% of the time against 26.9%. In credit reporting the largest weight by far is `equifax` (4.18), so much of that model is which bureau the complaint is about.
6. The single words aren't steady. With the model fitted on two halves of train, only 6 of the 20 largest weights towards a dispute are in both lists, and 4 of the 20 away from one (22 and 9 of the top 50). The groups do repeat in both halves: company names, legal wording and `attached` on one side, phone calls, fees and payday loans on the other. I read the lists as those groups, with the single words as examples.
7. The highest out-of-fold scores are Scottrade narratives (46 of the 100 highest). The lowest are one sentence in several wordings, "Experian is not responding to my requests to investigate and remove accounts", and 42 of the 100 lowest are about Experian. The grouped folds only keep narratives together when their first 100 characters match, so reworded copies like these still land on both sides of a fold.
8. The score goes up with length although the model has no length feature. The rank correlation between the score and the word count is 0.41, and the median narrative has 71 words in the lowest tenth of scores and 298 in the highest.

The company field from the first project already says which company a complaint is about, so the company names are the first place to look for overlap between the text and the fields in the next step.

## Text against fields, 15 Nov 2026

Everything is in notebooks/08_text_against_fields.ipynb. src/fields.py has `build_features()` from the complaint-escalation project, without channel and consent, and the two models that use its table. Three models are compared on the same complaints: the fields alone, the text alone (`chosen()`), and the fields with the text model's score added as one more column, `text_score`.

Cross-validation on train, on the grouped folds:

| Model | CV ROC-AUC | CV average precision |
| --- | ---: | ---: |
| Fields, logistic regression | 0.6263 | 0.3206 |
| Fields, XGBoost | 0.6277 | 0.3238 |
| Text | 0.6499 | 0.3640 |
| Fields and text score, logistic regression | 0.6759 | 0.3857 |
| Fields and text score, XGBoost | 0.6727 | 0.3810 |

The test set, 37,405 complaints from 1 Oct 2016 to 28 Feb 2017 with 20.8% disputed:

| Model | Test ROC-AUC | Test average precision | ROC-AUC without the 286 template letters |
| --- | ---: | ---: | ---: |
| Fields | 0.6260 | 0.2887 | 0.6263 |
| Text | 0.6419 | 0.3190 | 0.6407 |
| Fields and text score | 0.6709 | 0.3436 | 0.6698 |

1. The text score in the training rows is out-of-fold, from the same grouped 5-fold CV as before. A score from a model that had seen the complaint's own label would look better than it is, and the combined model would lean on the text too much. The test rows get their score from the text model fitted on all of train.
2. On their own the fields get 0.626 in CV with logistic regression and 0.628 with XGBoost at the first project's settings. The first project's logistic regression got 0.646 on all complaints. Channel and consent are constant here, so the fields have less to work with. The text alone is ahead at 0.650.
3. With the text score added, logistic regression gets 0.676 and XGBoost 0.673. The order of fields, text and both is the same in all five folds. Logistic regression went to the test run for the fields and for the combined model, since it's level with XGBoost on the fields and slightly ahead with the text score.
4. One caveat on the CV scores of the combined model. The text scores were made on the same folds, so the text model that scored a training fold had seen the validation fold's labels. A validation complaint's own text score never saw its own label, so the effect should be small, and the test run doesn't have this problem.
5. The company is where the text and the fields overlap. Without `company_share` and `company_rate` the fields drop from 0.626 to 0.607, but once the text score is in, the two columns are worth 0.003. The text adds 0.066 to fields without the company and 0.050 to fields with it, so about a quarter of what the text adds is the company.
6. On the test set the fields get 0.626 ROC-AUC, the text 0.642 and both together 0.671, the same order as in CV. The fields score what they did in CV, the text is 0.008 lower and the combined model 0.005 lower. Average precision is lower for all three because the dispute rate fell from 23.2% to 20.8%. Against the base rate the combined model is at 1.65 times on test and 1.66 in CV.
7. About a third of the text's drop from CV to test is Scottrade and RushCard. 619 training narratives mention one of them and 20 test narratives do, and without the 619 the text's out-of-fold ROC-AUC on train is 0.647 instead of 0.650.
8. Without the 286 test narratives that share an opening with a training narrative (77 are exact copies), the text and the combined model lose about 0.001 and the fields don't move. This is the score the split notes promised.
9. Resampling the test complaints 1,000 times, the combined model is 0.045 above the fields (95% interval 0.040 to 0.051) and 0.029 above the text (0.025 to 0.033). The text is 0.016 above the fields (0.008 to 0.024).
10. The combined model is the best of the three in all seven products with at least 2,000 test narratives. The text helps most where the fields are weakest: mortgages go from 0.562 with the fields to 0.634 with both, and student loans from 0.592 to 0.646. Bank accounts and consumer loans are the two products where the fields beat the text.
11. In the combined model one standard deviation in the text score moves the log-odds by 0.49, and the weight on `company_rate` falls from 0.26 to 0.14. The company's response keeps its weights (`Untimely response` near -3.1, `Closed` and `Closed with explanation` near 1.1 and 1.0), the three largest in both models. The consumer writes the narrative before the company answers, so the text can't know the response.
12. The test set was used once in this project, in this notebook. Before the project started, on 12 Nov, I did score a quick TF-IDF model and the first project's model on the same months, to see whether the text was worth a project (0.645 and 0.625). Every setting since then was picked on cross-validation.
13. The notebook saves the three scores for every complaint to data/scored_train.csv (out-of-fold) and data/scored_test.csv, for the decision step.

So the text does say something about disputes, a little more than the fields do on these complaints, and the two together are better than either. What that's worth to a team that reviews complaints is the next step.

## Decision, 16 Nov 2026

Everything is in notebooks/09_decision.ipynb. It reads the scores the last notebook saved, so the test set isn't scored again. The three models are compared on how many disputes are among the 10% of complaints with the highest scores. The 10% is an assumption about how much a team can review.

The top 10% of the test set, 3,740 of 37,405 complaints:

| Model | Disputes in the top 10% | Disputed among reviewed | Share of all disputes | Times random |
| --- | ---: | ---: | ---: | ---: |
| Fields | 1,199 | 32.1% | 15.4% | 1.54 |
| Text | 1,468 | 39.3% | 18.8% | 1.88 |
| Fields and text score | 1,564 | 41.8% | 20.1% | 2.01 |

1. The text adds 365 disputes to the top 10%, about 98 more for every 1,000 complaints reviewed. Resampling the test set 1,000 times gives a 95% interval of 81 to 115. The combined list has 96 more disputes than the text alone, about 26 per 1,000 (14 to 36).
2. The order is the same further down the list. At 20% the combined model catches 35.5% of all disputes and the fields 29.1%, and at 30% it's 48.0% against 42.2%. The gains chart is reports/figures/gains_curve.png.
3. The lift held from train to test. On the out-of-fold train scores the top 10% is at 1.57, 1.90 and 2.00 times the dispute rate for the three models.
4. The text changes most of the list. The fields list and the combined list share 1,436 complaints, and the 2,304 the text brings in were disputed 42.7% of the time against 26.9% for the 2,304 it replaces.
5. The overall list is uneven across companies. 24.2% of the narratives about Equifax and about JPMorgan Chase are on it, and 2.2% of those about Navient and Experian. A company's own team would rank inside its own complaints, where the company columns say nothing. Done that way for the 55 companies with at least 100 test narratives, the top 10% is 28.6% disputed with the fields, 38.0% with the text and 40.0% with both. The text adds about 114 disputes per 1,000 reviewed there, a little more than on the overall list, and the combined model is ahead of the fields in each of the eight largest companies.
6. Calibration. The models use balanced class weights, so the raw scores average 0.47 to 0.49 against a dispute rate of 23.2% in train. A logistic regression with one input, the log-odds of the score, fitted on the out-of-fold train scores, brings them back to the actual rate without changing the order. On test the combined model then predicts 22.5% against 20.8% actual, 1.7 points high, and each of the ten groups is high by 0.6 to 3.0 points. The dispute rate fell after the training months, and the first project had the same kind of gap (19.4% against 17.0%). The rescaling needs refitting on recent months before the score is shown as a probability.

Limitations and ethics:

7. A complaint without a narrative gets no text score. In the test months that's 50,034 of the 87,439 labelled complaints (57.2%): everything that came by phone, post, fax or referral, and 45.5% of web complaints. They only have the fields.
8. The narratives in the public file are from consumers who agreed to publish them, and their complaints are disputed more often (20.8% against 14.2% for the rest in the test months). Whether the text model works as well for the other consumers can't be tested with this data.
9. The list leans towards long narratives. 20.2% of the longest quarter (more than 250 words) are on the combined list and 3.7% of the shortest quarter (69 words or fewer). That follows the actual dispute rates, 26.8% and 15.9%, and the short narratives aren't scored below their rate. It still means a consumer who writes little is reviewed about a fifth as often, while 15.9% of the short narratives end in a dispute.
10. Servicemembers are on the combined list 8.6% of the time against 10.1% for untagged consumers, with the same dispute rate in the test months (20.7% and 20.9%). They disputed less often in train (21.7% against 23.4%) and the tag is one of the fields, so the models score them a little lower. With the fields alone it's 7.2%, so the text narrows the gap. Older Americans are at 9.5%.
11. A dispute is what the consumer did after the response. It doesn't say the company handled the complaint badly, and the explain step showed that the text model leans on legal wording and attached documents. So the list favours consumers who are likely to push back, and a team that only works from the list will see fewer of the ones who aren't.
12. Nothing here shows that reviewing a complaint prevents the dispute. "Caught" only means the complaint was on the list. The labels also end in April 2017, when CFPB stopped recording disputes, so all of this is on old data.

For a team that can review a tenth of its complaints, my choice is the combined model where there's a narrative and the fields where there isn't, ranked inside the company, with the rescaling refitted on recent months. The README, the summary and the Power BI page are the next step.
