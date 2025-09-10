import os
import sqlite3
import json
import copy
import itertools
import sqlite3

from tqdm import tqdm
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain.agents.agent_types import AgentType
from langchain.agents import initialize_agent
from langchain.docstore.document import Document
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.tools.retriever import create_retriever_tool
from dotenv import load_dotenv
load_dotenv()


# Paths
HF_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHROMADB_PERSIST_PATH = "./chromadb/"
DATA_BASE_PATH = r"C:\Users\OnkarPatil\Desktop\genai_data_quality\project\data"
DB_PATH = os.path.join(
    DATA_BASE_PATH, "conventional_power_plants", "conventional_power_plants.sqlite"
)
KB_PATHS = [
    os.path.join(DATA_BASE_PATH, "conventional_power_plants", "datapackage.json"),
]


def load_database(db_path=DB_PATH) -> Engine:
    """Engine for opsd data."""
    return create_engine(f"sqlite:///{db_path}", poolclass=StaticPool)


def filter_metadata(metadata):
    filtered_metadata = {}
    # filtered_metadata["name"] = metadata["name"]
    filtered_metadata["title"] = metadata["title"]
    filtered_metadata["description"] = metadata["description"]
    # filtered_metadata["longDescription"] = metadata["longDescription"]
    filtered_metadata["keywords"] = metadata["keywords"]
    if metadata.get("geographicalScope"):
        filtered_metadata["geographicalScope"] = metadata["geographicalScope"]
    if metadata.get("temporalScope"):
        filtered_metadata["temporalScope"] = metadata["temporalScope"]
    resources = metadata["resources"]
    filtered_resources = []
    for resource in resources:
        if (
            resource.get("schema")
            and resource.get("profile") == "tabular-data-resource"
        ):
            filtered_resource = {}
            filtered_resource["schema"] = resource["schema"]
            if resource.get("profile"):
                filtered_resource["profile"] = resource["profile"]
            if resource.get("title"):
                filtered_resource["title"] = resource["title"]
            if resource.get("name"):
                filtered_resource["name"] = resource["name"]
            filtered_resources.append(filtered_resource)
    filtered_metadata["resources"] = filtered_resources
    return filtered_metadata


def read_json(filename):
    with open(filename, "r") as f:
        data = json.load(f)
    return data


def split_json_custom(json_data):
    resources = json_data["resources"]
    filtered_resources = []
    for resource in resources:
        if resource.get("schema"):
            filtered_resource = {}
            if resource.get("title"):
                filtered_resource["table_description"] = resource["title"]
            if resource.get("name"):
                filtered_resource["table_name"] = resource["name"]
            resource_schema = resource["schema"]
            resource_schema_fields = resource_schema["fields"]
            filtered_resource["primary_key"] = resource_schema["primaryKey"]
            for field in resource_schema_fields:
                filt_resource_copy = copy.deepcopy(filtered_resource)
                field_resource = filt_resource_copy | field
                field_resource["column_name"] = field_resource.pop("name")
                filtered_resources.append(field_resource)
    return filtered_resources


def index_json_to_chromadb(kb_paths, db_persist_path, embedding_model):
    print("Indexing database json metadata to ChromaDB ...")
    documents = [filter_metadata(read_json(kb_path)) for kb_path in kb_paths]
    split_documents = [split_json_custom(json_data=doc) for doc in documents]
    splits = list(itertools.chain(*split_documents))
    splits = [Document(page_content=str(doc)) for doc in tqdm(splits)]
    chroma_vector_database = Chroma.from_documents(
        persist_directory=CHROMADB_PERSIST_PATH,
        documents=splits,
        embedding=embedding_model,
    )
    return chroma_vector_database


def load_chromadb_from_path(db_save_path, embedding_model):
    vector_db = Chroma(
        persist_directory=db_save_path, embedding_function=embedding_model
    )
    return vector_db


def get_vector_database_and_retriever_tool():
    embedding_model = HuggingFaceEmbeddings(model_name=HF_EMBEDDING_MODEL)
    # --- Index knowledge base against DB metadata (if not done already) ---
    if not os.path.exists(CHROMADB_PERSIST_PATH):
        vector_db = index_json_to_chromadb(
            KB_PATHS, CHROMADB_PERSIST_PATH, embedding_model
        )
    else:
        vector_db = load_chromadb_from_path(CHROMADB_PERSIST_PATH, embedding_model)
    retriever_tool = _create_retriever_tool(vector_db)

    return retriever_tool


def _create_retriever_tool(vector_db):
    retriever = vector_db.as_retriever(search_kwargs={"k": 10})
    retriever_tool = create_retriever_tool(
        retriever=retriever,
        name="search_db_metadata",
        description="Tool to retrieve relevant text chunks from a vector database",
    )
    return retriever_tool


def get_db_info_str(db_path=DB_PATH, time_series=False):
    # Connect to the SQLite database
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    # Query to get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Extract table names from the result
    table_names = [table[0] for table in tables]
    table_names_str = f"Tables: {table_names}"

    # Function to get column names for a given table
    def get_column_names(table_name):
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        return column_names

    column_info_str = ""
    # Get column names for each table
    for table in table_names:
        columns = get_column_names(table)
        # Apply filter to remove forecast columns in time-series dataset
        if time_series:
            final_columns = [
                column_name for column_name in columns if "load_actual" in column_name
            ]
            final_columns += [
                column_name for column_name in columns if "timestamp" in column_name
            ]
            column_info_str += f"Columns in {table}: {final_columns}\n"
        else:
            column_info_str += f"Columns in {table}: {columns}\n"
    return table_names, column_info_str

def react_agent(model, tools):
    return initialize_agent(
        tools=tools,
        llm=model,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    )

def fetch_results_from_db(sql_query):
    db_engine = load_database(db_path=DB_TIME_SERIES_PATH)
    db = SQLDatabase(db_engine)
    return eval(db.run(sql_query, include_columns=True))

