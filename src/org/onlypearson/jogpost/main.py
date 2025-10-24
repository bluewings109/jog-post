import uvicorn
from fastapi import FastAPI

from org.onlypearson.jogpost.app_config import create_app
from org.onlypearson.jogpost.di_container import Container

app: FastAPI = create_app()

container = Container()
container.wire()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7070)

