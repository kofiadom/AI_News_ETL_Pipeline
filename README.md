# What'sUpWithAI: An ETL Data Pipeline for Real-time AI News Updates

## Project Overview
**What'sUpWithAI** is an ETL (Extract, Transform, Load) data pipeline designed to fetch, process, and store real-time news updates on artificial intelligence. Utilizing Docker to host Airflow and leveraging Python scripts for data extraction and transformation, the pipeline ingests data into PostgreSQL and AWS S3 for efficient storage and analysis.

## Features
- **Real-time Data Extraction**: Fetches AI news updates from NewsAPI.
- **Data Transformation**: Processes raw JSON data into structured formats.
- **Data Ingestion**: Stores processed data in PostgreSQL and AWS S3.
- **Scalability**: Designed to handle increasing data volume and complexity.
- **Orchestration**: Utilizes Apache Airflow for task scheduling and monitoring.

## Technologies Used
- **Docker**: Containerization for consistent development and production environments.
- **Apache Airflow**: Orchestration and scheduling of ETL tasks.
- **Python**: Scripts for data extraction and transformation.
- **EventRegistry API**: Source for real-time AI news updates.
- **PostgreSQL**: Relational database for structured data storage.
- **AWS S3**: Scalable storage solution for large datasets.

## Project Interface
[![Docker Desktop](https://iili.io/2Jy2ICF.md.png)](https://freeimage.host/i/2Jy2ICF)

Docker Desktop



[![Running docker in the terminal](https://iili.io/2JyFgmQ.md.png)](https://freeimage.host/i/2JyFgmQ)

Running docker in the terminal



[![Airflow](https://iili.io/2Jyqzge.md.png)](https://freeimage.host/i/2Jyqzge)

Airflow



[![PgAdmin](https://iili.io/2JyB2EP.md.png)](https://freeimage.host/i/2JyB2EP)

PgAdmin



[![S3](https://iili.io/2JyC2t4.md.png)](https://freeimage.host/i/2JyC2t4)

S3



## Installation
### Prerequisites
- Docker Desktop
- Python 3.8+
- AWS Account
- Create your AWS access key id and aws secret access key
- Create your EventRegistry api key
- Copy and paste them in the respective variables in the newspipeline.py file.

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/kofiadom/AI_News_ETL_Pipeline
   cd AI_News_ETL_Pipeline
   ```

2. Open Docker Desktop
Ensure that Docker Desktop is running before you proceed.

3. Run docker commands
Run the following commands

```bash
docker compose up airflow-init
```

Once it finished running, run the following command

```bash
docker compose up
```

## Usage
1. Visit http://localhost:8080 to open Airflow in the browser to monitor the progress of data extraction, transformation, and ingestion tasks.
2. http://localhost:5050 to open PgAdmin to view the data in the postgres database.
3. Visit your AWS S3 bucket to view the data.


## Results
Achieved real-time data ingestion and processing.
Ensured data is securely stored and easily accessible in PostgreSQL and AWS S3.
Enabled timely and accurate AI news updates for stakeholders.
Streamlined the data management process, reducing manual intervention.


## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or new features.

## Acknowledgement
A thank you to Trestle Academy Ghana for the awesome data engineering training.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contact
If you face any challenge in the set-up, reach out to me on LinkedIn(https://www.linkedin.com/in/kofi-adom/)


