"""
Part I : Working with Spacy
"""

import spacy

nlp = spacy.load("en_core_web_sm")
doc = nlp("Apple buys U.K. startup for $1 Billion")

print(doc.ents)

for ent in doc.ents:
    print(ent.text, ent.label_)
"""
Output - 
Apple ORG
U.K. GPE
$1 Billion MONEY

"""