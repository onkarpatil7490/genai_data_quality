# GenAI Data Quality API

This project provides an API server for managing and testing **data quality rules**.  
Users can write rules in natural language, which are automatically converted to SQL, and then applied to validate or transform data as part of your ETL pipeline.  

## 🚀 Setup Guide

### 1. Create a Virtual Environment
python -m venv venv

Activate it:

Linux / macOS:
source venv/bin/activate

Windows:
venv\Scripts\activate

### 2. Install Requirements
pip install -r requirements.txt

### 3. Run the API Server
Navigate to the backend directory (if not already there) and start the server:

uvicorn main:app --reload

This will run the API server locally.  
Default URL → http://127.0.0.1:8000

### 4. Open the API Docs
1. Open your browser and go to http://127.0.0.1:8000  
2. At the end of the URL, add /docs and hit Enter  

You will see the **Swagger UI documentation** where you can test all APIs interactively.  

## 📂 Project Reference
Main backend entry point:  
https://github.com/onkarpatil7490/genai_data_quality/blob/main/project/dq_backend/main.py

## ✅ Next Steps
- Define and manage data quality rules using natural language.  
- Test the endpoints directly in the /docs page.  
- Integrate the rules with your ETL pipelines to validate and transform data automatically.  
