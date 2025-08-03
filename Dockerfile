FROM apache/airflow:2.7.1-python3.8

# Install required Python packages for the DAG
USER airflow
RUN pip install --no-cache-dir \
    confluent-kafka \
    elasticsearch \
    boto3
