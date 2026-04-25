---
title: "Optimize Data Retrieval in Python with Time-based API Pagination"
date: 2024-10-21 08:59:26 +0000
categories: [Apis]
tags: ["APIs", "FastAPI", "Python", "sqlalchemy"]
image:
  path: https://cdn.hashnode.com/res/hashnode/image/stock/unsplash/I84vGUYGUtQ/upload/93b6b1e6924ceb8f93c712dee97a23f4.jpeg
---

In the modern application development, APIs(Application Programming Interfaces) serve as the core mechanism for connecting various systems and enabling seamless data exchange.

An API is a way for different software systems to communicate with one another. It allows developers to create applications that use data and functionality provided by other software systems.

Major challenge developers encounter when working with large datasets is how to handle large amounts of data. APIs often return large datasets and working with this data can both be time-consuming and resource-intensive. Here is where pagination comes in to save the day.

### What is API Pagination

Pagination is a technique for breaking up large datasets into smaller more manageable chunks of data. Instead of returning the entire dataset in one response, an API can return a subset of the data along with metadata that describes the overall dataset

There are different techniques of doing pagination but here we will specifically look into time-based pagination. Time-based pagination involves using time-related parameters such as “start-time” and “end-time” to specify a time range for retrieving data.

### Prerequisites

Before starting, ensure you have the following installed:

* Python 3.12
    
* FastAPI
    
* Uvicorn
    
* SQLAlchemy
    

### Dependencies Installation

Install the necessary dependencies with the following command:

```bash
pip install fastapi uvicorn sqlalchemy
```

### Setting up The Database Models

For our example, we will use use journals as our database model. In database.py, define the model and set a database connection.

```python
from sqlalchemy import create_engine, Integer, String, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()

class Journal(Base):
    __tablename__ = "journals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"""
                id={self.id},
                content={self.content},
                created_at={self.created_at}"""

def db_connection():
    engine = create_engine(db_url="your_db_url_here")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bing=engine, autocommit=False, autoflush=False)
    return Session()
```

In the above python script, we are defining our Journal model in the Journal class. Then in the db\_connection function, we create a connection to the database using SQLAlchemy.

Now let’s say we have several records of journals in our database and for a specific user, we want to be able to retrieve their journals for the current week and the current month. Let’s dive into the python code below.

```python
from datetime import datetime, timedelta, UTC

def get_week_range():
    today = datetime.now(UTC)
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week

def get_month_range():
    today = datetime.now(UTC)
    start_of_month = today.replace(day=1)
    next_month = today.replace(day=28) + timedelta(days=4)
    end_of_month = next_month.replace(day=1) - timedelta(days=1)
    return start_of_month, end_of_month
```

In the above code, we are trying to get the start and end of week and month dates depending on the current date.

Now over to our endpoints where we define the path operations to get journals.

```python
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

db = db_connection()
router = APIRouter()

@router.get("/journals")
async def get_journals(filter_by: str=Query(...)):
    if filter_by=="week":
        start_date, end_date = get_week_range()
    elif filter_by=="month":
        start_date, end_date = get_month_range()
    else:
        raise HTTPException(status_code=400, detail="Invalid filter option. Valid options are 'week' and 'month'")
    query = select(Journal).where(Journal.created_at.between(start_date, end_date))
    results = db.execute(query)scalars().all()
    return results
```

### Main Application

Set up the FastAPI application

```python
from fastapi import FastAPI
from .routes import router

app = FastAPI(docs_url="/")
app.include_router(router, prefix="/api/v1")
```

### Running The Application

To run the application, use Uvirorn.

```bash
uvicorn main:app --reload
```

### Conclusion

now you have a gist of what time-based pagination entails and how to implement it in FastAPI. If you are planning to use the code above in your production, consider adding features like error handling and organizing the code in a clean architecture to ensure it’s easier to work with.

Happy hacking🙂
