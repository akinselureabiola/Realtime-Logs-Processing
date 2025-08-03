import logging
import re
from datetime import timedelta, datetime
import json

from airflow import DAG
from airflow.operators.python import PythonOperator

# The following libraries are now installed via the Dockerfile
# and should be available.
from confluent_kafka import Consumer, KafkaException
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# Define logger for the DAG
logger = logging.getLogger(__name__)

# Mock get_secret function for local development and to get the DAG loading.
# This avoids a separate utils.py file and simplifies the startup process.
def get_secret(secret_name):
    """
    This is a placeholder function to simulate fetching secrets.
    Replace these placeholder values with your actual credentials for local testing.
    """
    logger.info(f"Simulating fetching secret for: {secret_name}")
    return {
        "KAFKA_BOOTSTRAP_SERVER": "your-kafka-server:9092",
        "KAFKA_SASL_USERNAME": "your-kafka-username",
        "KAFKA_SASL_PASSWORD": "your-kafka-password",
        "ELASTICSEARCH_URL": "http://elasticsearch:9200",
        "ELASTICSEARCH_API_KEY": "your-elasticsearch-api-key"
    }


def parse_log_entry(log_entry):
    """
    Parses a single log entry using a regular expression.
    A common log format is similar to: 127.0.0.1 - - [17/Mar/2024:14:00:00 +0000] "GET /home HTTP/1.1" 200 123
    """
    # This regex is for a common Apache log format.
    log_pattern = r'(?P<ip>[\d\.]+) - - \[(?P<timestamp>[\w/]+:[\d:]+) (?P<timezone>[\w\+\-]+)\] "(?P<method>\w+) (?P<endpoint>[\w/]+) (?P<protocol>[\w/\.]+)"'
    match = re.match(log_pattern, log_entry)
    if not match:
        logger.warning(f"Invalid log format: {log_entry}")
        return None

    data = match.groupdict()

    try:
        parsed_timestamp = datetime.strptime(data['timestamp'], '%d/%b/%Y:%H:%M:%S')
        data['@timestamp'] = parsed_timestamp.isoformat()
    except ValueError:
        logger.error(f"Timestamp parsing error: {data['timestamp']}")
        return None

    return data


def consume_and_index_logs(**context):
    """
    Consumes logs from Kafka and indexes them into Elasticsearch.
    """
    # Using the mock function defined in this file.
    secrets = get_secret("MWAA_Secrets_V2")

    consumer_config = {
        'bootstrap.servers': secrets['KAFKA_BOOTSTRAP_SERVER'],
        'security.protocol': 'SASL_SSL',
        'sasl.mechanisms': 'PLAIN',
        'sasl.username': secrets['KAFKA_SASL_USERNAME'],
        'sasl.password': secrets['KAFKA_SASL_PASSWORD'],
        'group.id': 'mwaa_log_indexer',
        'auto.offset.reset': 'latest'
    }

    es_config = {
        'hosts': [secrets['ELASTICSEARCH_URL']],
        'api_key': secrets['ELASTICSEARCH_API_KEY']
    }

    consumer = Consumer(consumer_config)
    es = Elasticsearch(**es_config)
    topic = 'billion_website_logs'
    consumer.subscribe([topic])

    try:
        index_name = 'billion_website_logs'
        if not es.indices.exists(index=index_name):
            es.indices.create(index=index_name)
            logger.info(f'Created index: {index_name}')

    except Exception as e:
        logger.error(f'Failed to create index: {index_name} - {e}')

    logs = []
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                break

            if msg.error():
                if msg.error().code() == KafkaException._PARTITION_EOF:
                    break
                raise KafkaException(msg.error())

            log_entry = msg.value().decode('utf-8')
            parsed_log = parse_log_entry(log_entry)

            if parsed_log:
                logs.append(parsed_log)

            if len(logs) >= 15000:
                actions = [
                    {
                        '_op_type': 'create',
                        '_index': index_name,
                        '_source': log
                    }
                    for log in logs
                ]

                success, failed = bulk(es, actions, refresh=True)
                logger.info(f'Indexed {success} logs, {len(failed)} failed')
                logs = []
    except Exception as e:
        logger.error(f'Failed to index log: {e}')

    try:
        if logs:
            actions = [
                {
                    '_op_type': 'create',
                    '_index': index_name,
                    '_source': log
                }
                for log in logs
            ]
            bulk(es, actions, refresh=True)
            logger.info(f'Indexed final batch of {len(logs)} logs.')
    except Exception as e:
        logger.error(f'Log Processing error: {e}')
    finally:
        consumer.close()
        es.close()


default_args = {
    'owner': 'Data Mastery Lab',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=5)
}


with DAG(
    'log_consumer_pipeline',
    default_args=default_args,
    description='Consume and Index synthetic logs',
    schedule='*/5 * * * *',
    start_date=datetime(year=2025, month=8, day=2),
    catchup=False,
    tags=['logs', 'kafka', 'production']
) as dag:
    consume_logs_task = PythonOperator(
        task_id='generate_and_consume_logs',
        python_callable=consume_and_index_logs,
    )
