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
This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

Place your AI Chatbot API in backend/.env file


```bash
In folder src/app run 

npm install

npm run dev
```

Open [http://localhost:3000/rule_creation](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/`. The page auto-updates as you edit the file.

backend is using fastapi

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
