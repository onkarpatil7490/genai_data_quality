# GenAI Data Quality APIs

This project provides an API server for managing and testing **data quality rules**.  
Users can write rules in natural language, which are automatically converted to SQL, and then applied to validate or transform data as part of your ETL pipeline.  

## 🚀 Setup Guide

### 1. Create a Virtual Environment
Command: python -m venv venv

Activate it:

Windows:
Command: venv\Scripts\activate

### 2. Install Requirements
Command: pip install -r requirements.txt

### 3. Run the API Server

Navigate to the below path and start the server:

https://github.com/onkarpatil7490/genai_data_quality/blob/main/project/dq_backend

Command: uvicorn main:app --reload

This will run the API server locally.  
Default URL → http://127.0.0.1:8000

### 4. Open the API Docs
1. Open your browser and go to http://127.0.0.1:8000  
2. At the end of the URL, add "/docs" and hit Enter  

You will see the **Swagger UI documentation** where you can test all APIs interactively.   


## ✅ Next Steps
- Test the endpoints directly in the /docs page.    
