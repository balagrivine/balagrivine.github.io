---
title: "FastAPI Tutorial: Creating a CRUD Application Easily"
date: 2024-10-19 14:54:20 +0000
categories: [Fastapi]
tags: ["FastAPI", "sqlalchemy", "Python"]
image:
  path: https://cdn.hashnode.com/res/hashnode/image/stock/unsplash/KOr1LG2TIPs/upload/89baf2d986d612684d41351ff07e7bdf.jpeg
---

FastAPI is a modern, fast(high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints. FastAPI uses ASGI(Asynchronous Server Gateway Interface) instead of WSGI. ASGI supports asynchronous programming, which allows FastAPI to handle multiple requests concurrently.

### Prerequisites🗒️

Before starting, ensure you have the following installed:

* Python 3.7+
    
* FastAPI
    
* Uvicorn
    
* SQLAlchemy (for database interactions)
    

### Dependencies Installation

Install the necessary dependencies with the following command:

```bash
pip install fastapi uvicorn sqlalchemy
```

### Setting Up The Database

First, we’ll set up our database configuration.

### Database Models

In database.py, set up the database connection:

```python
from sqlalchemy import create_engine, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Article(Base):
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)

engine = create_engine(url="your_database_url")
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
session = Session()

def get_db():
    try:
        db = session
        yield db
     finally:
        db.close()
```

### CRUD Operations

In crud.py implement CRUD operations:

```python
from fastapi import APIRouter, HTTPException
from .database import get_db

router = APIRouter()
db = get_db()

@router.get("/articles")
async def get_articles():
    return db.Query(Article).all()

@router.post("/articles")
async def create_article(title: str, content: str):
    article = Article(
        title=title,
        content=content)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article

@router.patch("/articles/{article_id}")
async def update_article(article_id: int, content: str):
    article = db.Query(Article).filter(Article.id==article_id).first()
    if article:
        article.content = content
        db.add(article)
        db.commit()
        return article
    else:
        raise HTTPException(status_code=400, detail="Invalid article id")

@router.delete("/articles/{article_id}")
async def delete_article(article_id: int):
    article = db.Query(Article).filter(Article.id==article_id).first()
    if article:
        db.delete(article)
        db.commit()
        return
    else:
        raise HTTPException(status_code=400, detail="Invalid article id")
```

### Main Application

In main.py set up the FastAPI application:

```python
from fastapi import FastAPI
from .crud import router

app = FastAPI(docs_url="/")

app.include_router(router, prefix="/api/v1")
```

### Running the application

Tu run the application, use Uvicorn:

```bash
uvicorn main:app --reload
```

You can now move over to [http://127.0.0.1:8000](http://127.0.0.1:8000) to access the interactive API documentation.

### Conclusion

In this article, we walked through the steps to create a simple CRUD application using FastAPI. We covered configuring the database, creating models, implementing CRUD operations and defining API routes. FastAPI’s speed. ease of use, and automatic documentation makes it an excellent choice for building web APIs.

Happy hacking🙂
