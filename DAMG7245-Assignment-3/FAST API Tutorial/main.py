"""
Part II : Introduction to FAST API

Last update : Code is till 51:02 in YT video

https://www.youtube.com/watch?v=1zMQBe0l1bM&ab_channel=AbhishekThakur
"""

from fastapi import FastAPI
from spacyML import nlp
from typing import List
# for data handling fast api is built on pydantic
from pydantic import BaseModel
# for web based handling fast api is built on starlette
import starlette

app = FastAPI()


@app.get("/")
def read_main():
    return {"message": "Hello World"}


"""
Adding another path operation
-----------------------------

http://127.0.0.1:8000/article/56?q=hello 
When we pass q, which is not part of path parameter but of query parameter, its taken by the API like above URL
"""


@app.get("/article/{article_id}")
def analyse_article(article_id: int, q: str = None):
    count = 0
    if q:
        doc = nlp(q)
        count = len(doc.ents)
    return {"article_id": article_id, "previous_id": article_id - 1, "q": count}


"""
Output:
{
  "article_id": 56,
  "previous_id": 55,
  "q": 3
}
"""


class Article(BaseModel):
    content: str
    comments: List[str] = []  # Using default value as [], we prevent error if comments is not passed


# Send data using Post method
@app.post("/article/")
def post_article(articles: List[Article]):
    # logic for model import predict etc
    """
    Analyse an article and extract entities using 🌟 spaCy 🌟

    Statistical models *will* have **errors**
    * Extract entities
    * Scream Comments
    """

    ents = []
    comments = []
    for article in articles:
        for comment in article.comments:
            comments.append(comment.upper())
        doc = nlp(article.content)
        for ent in doc.ents:
            ents.append({"text": ent.text, "label": ent.label_})
    return {"ents": ents, "comments": comments}
