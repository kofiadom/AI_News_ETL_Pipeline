from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import os
import json
import pandas as pd
import psycopg2
import boto3
import pathlib
import logging
from eventregistry import EventRegistry, QueryArticlesIter, QueryItems

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define functions
def extract_data(**kwargs):
    api_key = os.getenv('NEWS_API_KEY')
    if not api_key:
        raise ValueError("No API key found in environment variables. Please set 'NEWS_API_KEY'.")

    er = EventRegistry(apiKey=api_key)

    query = QueryArticlesIter(
        keywords=QueryItems.OR(["artificial intelligence", "machine learning", "deep learning", "natural language processing", "computer vision"]),
        lang="eng",
        dataType=["news", "blog"],  # news articles and blogs
        isDuplicateFilter="skipDuplicates"  # skip duplicate articles
    )

    articles = [article for article in query.execQuery(er, sortBy="date", maxItems=1000)]

    os.makedirs('data', exist_ok=True)

    with open('data/ai_news_articles.json', 'w') as file:
        json.dump(articles, file, indent=4)

    df = pd.DataFrame(articles)
    columns_to_keep = ['uri', 'lang', 'date', 'time', 'url', 'title', 'body', 'authors', 'image']
    df = df[columns_to_keep]
    df.to_csv('data/ai_news_articles.csv', index=False)

    logger.info(f'Successfully saved {len(articles)} articles to ai_news_articles.json and ai_news_articles.csv')
    return df

def load_data_to_postgres(**kwargs):
    ti = kwargs['ti']
    df = ti.xcom_pull(task_ids='extract_data')

    conn_string = "dbname='postgres' user='postgres' host='postgres' password='harold'"
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    table_name = 'news_articles'
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

    for _, row in df.iterrows():
        cur.execute(f"""
        INSERT INTO {table_name} (uri, lang, date, time, url, title, body, authors, image)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            row['uri'], row['lang'], row['date'], row['time'], row['url'], row['title'], row['body'], 
            json.dumps(row['authors']), row['image']
        ))

    conn.commit()
    cur.close()
    conn.close()

    logger.info(f'Successfully loaded data into {table_name} table')

def upload_file_to_s3(**kwargs):
    s3 = boto3.client(
        service_name="s3",
        region_name="eu-north-1",
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    bucket_name = "ai-news-pipeline"
    object_name = "ai_news_articles.csv"
    file_name = os.path.join(pathlib.Path(__file__).parent.resolve(), "data/ai_news_articles.csv")

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
extract_task >> load_task >> upload_task
