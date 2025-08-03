# Real-time Log Processing Pipeline

This repository hosts an Apache Airflow-orchestrated pipeline for generating, queuing, and indexing synthetic web server logs in real-time. It leverages Apache Kafka for robust message handling and Elasticsearch for powerful log storage and analysis.

## 🚀 Features

  * **Synthetic Log Generation:** Creates realistic web server access logs using the `Faker` library.
  * **Kafka Integration:** Publishes logs to Apache Kafka for high-throughput, fault-tolerant message queuing.
  * **Elasticsearch Indexing:** Consumes logs from Kafka, parses them, and indexes them into Elasticsearch for real-time search and analytics.
  * **Airflow Orchestration:** Manages the entire pipeline's scheduling, execution, and monitoring with Apache Airflow.
  * **Scalable Architecture:** Built with components designed for horizontal scaling (Kafka, Elasticsearch).
  * **Secure Secrets Management:** Supports flexible secret handling, from local placeholders to AWS Secrets Manager in production environments.

## 🏗️ Architecture Overview

The pipeline operates in a flow:

1.  **`logs_producer.py` (Airflow DAG):** Generates synthetic logs and publishes them to a Kafka topic named `billion_website_logs`.
2.  **Apache Kafka:** Acts as a central message broker, receiving and temporarily storing log events.
3.  **`log_processing_pipeline.py` (Airflow DAG):** Consumes logs from the `billion_website_logs` Kafka topic, parses them into a structured format, and then indexes them into the `billion_website_logs` index in Elasticsearch.
4.  **Elasticsearch:** Stores the processed, structured log data, enabling quick search and analysis.
5.  **Apache Airflow:** Orchestrates the execution and scheduling of both the producer and consumer DAGs.

## 🏁 Getting Started

This project can be set up locally using Docker Compose or deployed to AWS MWAA for production.

### Local Setup (Docker Compose)

For development and testing:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/real-time-log-processing.git
    cd real-time-log-processing
    ```
2.  **Set up Virtual Environment & Install Dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: .\venv\Scripts\activate
    pip install -r requirements.txt
    pip install apache-airflow # Ensure Airflow is installed in your venv
    ```
3.  **Configure Local Secrets:**
      * **`utils.py` & `log_processing_pipeline.py`:** Update the `get_secret` mock functions with your local Kafka (e.g., `localhost:9092`) and Elasticsearch (e.g., `http://localhost:9200`) connection details.
4.  **Start Docker Services:** (Assumes a `docker-compose.yml` is present for Kafka, Elasticsearch, Airflow)
    ```bash
    docker-compose up -d
    ```
5.  **Access Airflow UI:** Navigate to `http://localhost:8080`, log in (default: `airflow`/`airflow`), and **unpause** the `logs_producer` and `log_consumer_pipeline` DAGs. Trigger `logs_producer` first.

### AWS MWAA Setup (Production)

For a production environment using AWS MWAA:

1.  **S3 Bucket:** Upload your DAGs (`logs_producer.py`, `log_processing_pipeline.py`, `utils.py`) to the `dags/` folder in your MWAA S3 bucket, and `requirements.txt` to the root.
2.  **MWAA Environment:** Create an MWAA environment, linking your S3 bucket and specifying `requirements.txt`.
3.  **AWS Secrets Manager:**
      * Create a secret named `MWAA_Secrets_V2` in AWS Secrets Manager.
      * Store your production Kafka and Elasticsearch credentials in this secret as a JSON string (e.g., `KAFKA_BOOTSTRAP_SERVER`, `KAFKA_SASL_USERNAME`, `ELASTICSEARCH_URL`, etc.).
      * Ensure your MWAA execution role has `secretsmanager:GetSecretValue` permissions for this secret.
4.  **Airflow UI:** Access your MWAA Airflow UI and **unpause** both DAGs.

## 📂 Project Structure

```
.
├── dags/
│   ├── logs_producer.py              # Airflow DAG for log generation and Kafka publishing
│   ├── log_processing_pipeline.py    # Airflow DAG for Kafka consumption and Elasticsearch indexing
│   └── utils.py                      # Helper functions, including secret retrieval placeholder
├── requirements.txt                  # Python dependencies
└── README.md
```

## ⚙️ Configuration & Secrets

  * **Kafka Topic:** Both DAGs interact with the `billion_website_logs` Kafka topic.
  * **Elasticsearch Index:** Logs are indexed into `billion_website_logs` in Elasticsearch.
  * **Secrets:**
      * **Local:** `utils.py` and `log_processing_pipeline.py` contain mock `get_secret` functions for local testing.
      * **Production:** `logs_producer.py` uses `boto3` to fetch secrets from AWS Secrets Manager (secret name: `MWAA_Secrets_V2`).
      * **Crucial:** Never hardcode sensitive credentials directly in code committed to Git.
