from __future__ import annotations
import pendulum
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
import time
import logging
from datetime import timedelta
from faker import Faker
from confluent_kafka import Producer
import boto3.session
import json
import random


fake = Faker()
logger = logging.getLogger(__name__)

def create_kafka_producer(config):
    return Producer(config)



def generate_log():
    """Generate synthetic log"""
    methods = ['GET', 'POST', 'PUT', 'DELETE']
    endpoints = ['/api/users', '/home', '/about', '/contact', 'services']
    statuses = [200, 302, 302, 400, 404, 500]

    user_agents = [
        'Mozilla/5.0 (iphone; CPU iphone OS 14_6 like Mac OS X)',
        'Mozilla/5.0 (X11; Linux x86_64)',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64 )',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebkit/537.36 (KHTML, like Gaeko) Chrome/91.0.4472.124 Safari/537.36'
    ]

    referrers = ['https://example.com', 'https://google.com', '-', 'https://bingo.com', 'https://yahoo.com']

    ip = fake.ipv4()
    timestamp = datetime.now().strftime('%b %d %Y, %H:%M:%S')
    method = random.choice(methods)
    endpoint = random.choice(endpoints) 
    status = random.choice(statuses)
    size = random.randint(1000,15000)
    referrer = random.choice(referrers)
    
    user_agent = random.choice(user_agents)
    log_entry = (
        f'{ip} - - [{timestamp}] "{method} {endpoint} HTTP/1.1" {status} {size} "{referrer}" "{user_agent}"'
    )

    return log_entry

def delivery_report(err, msg):
    if err is not None:
        logger.error(f'Message delivery failed: {err}')
    else:
        logger.info(f'Message delivered to {msg.topic()} [{msg.partition()}]')

def get_secret(secret_name, region_name='eu-central-1'):
    """Retrieve secrets from AWS secret Manager"""
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        logger.error(f"Secret retrieval error: {e}")
        raise

def produce_logs(**context):
    """Produce log entries into kafka"""
    secrets = get_secret('MWAA_Secrets_V2')
    kafka_config = {
        'bootstrap.servers': secrets['KAFKA_BOOTSTRAP_SERVER'],
        'security.protocol': 'SASL_SSL',
        'sasl.mechanisms': 'PLAIN',
        'sasl.username': secrets['KAFKA_SASL_USERNAME'],
        'sasl.password': secrets['KAFKA_SASL_PASSWORD'],
        'session.timeout.ms': 50000
    }

    producer = create_kafka_producer(kafka_config)
    topic = 'billion_website_logs'

    for _ in range(15000):
        log = generate_log()
        try:
            print(f"Producing to topic: {topic}")
            producer.produce(topic, log.encode('utf-8'), on_delivery=delivery_report)
        except Exception as e:
            logger.error(f'Error producing log: {e}')
            raise
    producer.flush()

    logger.info(f'Produced 15,000 logs to topic {topic}')

def produce_logs_task():
    """A placeholder Python function to simulate log production."""
    print("Simulating log production...")
    time.sleep(5)
    print("Log production complete.")

default_args = {
    'owner': 'Data Mastery Lab',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=5)
}

with DAG(
    dag_id="logs_producer",
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"),
    schedule=None,
    catchup=False,
    tags=["log_pipeline"],
) as dag:
    produce_logs = PythonOperator(
        task_id="produce_logs",
        python_callable=produce_logs_task,
    )

