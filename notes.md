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
