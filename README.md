# Runner
Running Log &amp; Race Predictor

# 1 App Overview
- Single Page Running Dashboard
    - Mileage Trends
    - Running Activity Log
- Frontend
    - ReactJS
    - TailwindCSS
- Backend
    - Python / FastAPI
        - CRUD
            - POST /runs
            - GET /runs?
            - GET /runs?start_date=&end_date= (for weekly window)
	        - PUT /runs/{id}
	        - DELETE /runs/{id}
        - Aggregates for charts:
	        GET /stats/weekly-mileage?weeks=12
- DB
    - PostgreSQL
        - Schema
            - date
            - title
            - notes
            - distance mi
            - duration HH:MM:SS
            - pace 6:30/mi
