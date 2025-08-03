# Real-time Log Processing Pipeline

This repository hosts an Apache Airflow-orchestrated pipeline for generating, queuing, and indexing synthetic web server logs in real-time. It leverages Apache Kafka for robust message handling and Elasticsearch for powerful log storage and analysis.

##  Features

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
