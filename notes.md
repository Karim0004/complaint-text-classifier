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
