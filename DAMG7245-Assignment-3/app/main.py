# generated by fastapi-codegen:
#   filename:  fastapiTest.yaml
#   timestamp: 2022-03-04T22:10:31+00:00

from __future__ import annotations

from typing import Union

from fastapi import FastAPI, Path

from .models import Error, Weatherviz

app = FastAPI(
    version='1.0.0',
    title='SEVIR Data Nowcasting',
    license={'name': 'MIT'},
    servers=[{'url': 'http://sevir-nowcasting.streamlit.io/v1'}],
)


@app.get(
    '/weatherviz', response_model=Weatherviz, responses={'default': {'model': Error}}
)
def weather_by_event_id(
    event_id: str = Path(..., alias='eventId')
) -> Union[Weatherviz, Error]:
    """
    Weather Visualization Info for a eventId
    """
    pass


@app.post('/weatherviz', response_model=None, responses={'default': {'model': Error}})
def generate_nowcast() -> Union[None, Error]:
    """
    Generate Nowcast Images
    """
    pass
