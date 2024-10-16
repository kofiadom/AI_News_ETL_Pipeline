import os
import pathlib
import logging
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to extract data
def extract_data(**kwargs):
    import pandas as pd
    import json
    from eventregistry import EventRegistry, QueryArticlesIter, QueryItems

    api_key = " "
    if not api_key:
        raise ValueError("No API key found in environment variables. Please set 'NEWS_API_KEY'.")

    # Initialize EventRegistry with your API key
    er = EventRegistry(apiKey=api_key)

    query = QueryArticlesIter(
        keywords=QueryItems.OR(["artificial intelligence", "machine learning", "deep learning", "natural language processing", "computer vision"]),
        lang="eng",
        dataType=["news", "blog"],  # news articles and blogs
        isDuplicateFilter="skipDuplicates"  # skip duplicate articles
    )

    # Fetch articles
    articles = []
    for article in query.execQuery(er, sortBy="date", maxItems=100):
        articles.append(article)

    # Ensure the 'data' directory exists
    os.makedirs('data', exist_ok=True)

    # Save the articles to a JSON file
    with open('ai_news_articles.json', 'w') as file:
        json.dump(articles, file, indent=4)

    # Create a DataFrame from the fetched articles
    df = pd.DataFrame(articles)

    # Keep only the required columns
    columns_to_keep = ['uri', 'lang', 'date', 'time', 'url', 'title', 'body', 'authors', 'image']
    df = df[columns_to_keep]

    # Save the DataFrame to a CSV file
    csv_file_path = '/opt/airflow/data/ai_news_articles.csv'  # specify the full path
    df.to_csv(csv_file_path, index=False)

    print(f'Successfully saved {len(articles)} articles to ai_news_articles.json and ai_news_articles.csv')
    kwargs['ti'].xcom_push(key='extract_data', value=df)

    return df

# Function to load data into PostgreSQL
def load_data_to_postgres(**kwargs):
    import psycopg2
    import json
    import numpy as np

    df = kwargs['ti'].xcom_pull(key='extract_data', task_ids='extract_data')
    table_name = 'news_articles'
    conn_string = "dbname='airflow' user='airflow' host='postgres' port='5432' password='airflow'"

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    # Create the table if it doesn't exist
    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        uri TEXT,
        lang TEXT,
        date DATE,
        time TIME,
        url TEXT,
        title TEXT,
        body TEXT,
        authors JSONB,
        image TEXT
    );
    """)

    # Insert each record into the table
    for index, row in df.iterrows():
        authors_list = row['authors'].tolist() if isinstance(row['authors'], np.ndarray) else row['authors']
        cur.execute(f"""
        INSERT INTO {table_name} (uri, lang, date, time, url, title, body, authors, image)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            row['uri'], row['lang'], row['date'], row['time'], row['url'], row['title'], row['body'], 
            json.dumps(authors_list), row['image']
        ))

    # Commit the transaction
    conn.commit()

    # Close the cursor and connection
    cur.close()
    conn.close()

    print(f'Successfully loaded data into {table_name} table')

# Extract data
'''
df = extract_data()

# Load data into PostgreSQL
table_name = 'news_articles'
conn_string = "dbname='airflow' user='airflow' host='postgres' password='airflow'"

load_data_to_postgres(df, table_name, conn_string)
'''

def upload_file_to_s3(**kwargs):
    import boto3

    s3 = boto3.client(
        service_name="s3",
        region_name="eu-north-1",
        aws_access_key_id=" ",
        aws_secret_access_key=" "
    )
    
    bucket_name = "ai-news-pipeline"
    object_name = "ai_news_articles.csv"
    file_name = '/opt/airflow/data/ai_news_articles.csv'  # use the same path as in extract_data
    
    # Check if the file exists
    if not os.path.isfile(file_name):
        logger.error(f"File not found: {file_name}")
        return

    try:
        s3.upload_file(file_name, bucket_name, object_name)
        logger.info(f"File uploaded successfully to {bucket_name}/{object_name}")
    except Exception as e:
        logger.error(f"Error uploading file: {e}")


# Define default_args
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define DAG
dag = DAG(
    'etl_data_pipeline',
    default_args=default_args,
    description='ETL pipeline for uploading data to S3 and storing it in PostgreSQL',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
)

# Define tasks
extract_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data,
    provide_context=True,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_data_to_postgres',
    python_callable=load_data_to_postgres,
    op_kwargs={'df': '{{ ti.xcom_pull("extract_data") }}', 
               'table_name': 'news_articles', 
               'conn_string': "dbname='airflow' user='airflow' host='postgres' port='5432' password='airflow'"},
    provide_context=True,
    dag=dag,
)

upload_task = PythonOperator(
    task_id='upload_file_to_s3',
    python_callable=upload_file_to_s3,
    provide_context=True,
    dag=dag,
)

# Set task dependencies
extract_task >> [load_task, upload_task]
