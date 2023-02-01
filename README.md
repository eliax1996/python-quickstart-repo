# Python Healthcheck

This project is a simple healthcheck for a set of configurable websites.
It includes two running components:

1. an Http fetcher that fetches the websites and forward the result to a Kafka topic (called in the code Healthcheck
   producer)
2. a Kafka consumer that consumes the messages from the topic and stores them one or more Postgres database tables (
   called in the code Healthcheck consumer)

## running the program locally

The ci/cd pipeline is configured to run the program in a docker container.
The docker container is built and pushed to the `docker run eliax1996/python-quickstart-project` docker image.
Every time there is a new release, the ci detects it and pushes the new version to the docker image.
Currently, the last tag is `0.0.1`.

Start by cloning the repository, enter in the project and start the docker compose by running the following command:

```bash
docker-compose up
```

This will start the postgres database, the kafka broker and the zookeeper.

The project is using the ci to construct a docker image with the required dependencies.

To run the consumer locally, after having configured the environment variables, and the `config.yaml` file, run the
following command to create the consumer:

```bash
docker run eliax1996/python-quickstart-project:16-SNAPSHOT --consumer -c config.yaml
```

And then run the following command to create the producer:

```bash
docker run eliax1996/python-quickstart-project:16-SNAPSHOT --producer -c config.yaml
```

From this point you have a running consumer and producer that will fetch the websites and store the results in the
database.
If you want to check the results, you can connect to the postgres database and execute a query on the configured table
to see the results.

Supposing that you have configured the table name to be `healthcheck`, you can run the following query to see the
results:

```bash
docker exec -it postgresql psql -U admin -d healthcheck -c "select * from healthcheck"
```

And you should see something like this:

| url_digest | measurement_time | response_time_microseconds | uri   | status_code | regex_present | regex_match |
|------------|------------------|----------------------------|-------|-------------|---------------|-------------|
| 09f0bcc... | 2021-03-01 12... | 239656                     | ww... | 200         | f             |             |
| 3e4fcea... | 2021-03-01 12... | 333551                     | ww... | 200         | y             | y           |
| ...        | ...              | ....                       | ...   | ...         | ...           | ...         |

## running the program using external services

The program can be run using external services, such as a postgres database and a kafka broker.
To do so, you need to configure the `config.yaml` enabling him to read your environment variables.
An example of the configuration is the following:

```yaml
healthcheck-producer-config:
  bootstrap_servers:
    - !ENV ${BOOTSTRAP_SERVER}
  security_protocol: "SSL"
  ssl_cafile: !ENV ${CA_FILE}
  ssl_certfile: !ENV ${CERT_FILE}
  ssl_keyfile: !ENV ${KEY_FILE}
  websites:
    - url: https://www.google.com
      polling_interval_in_seconds: 30
      regex: .*google.*
      destination_topic: healthcheck-topic-cloud-providers
    - url: https://www.amazon.com
      polling_interval_in_seconds: 10
      regex: .*amazon.*
      destination_topic: healthcheck-topic-cloud-providers
healthcheck-consumer-config:
  bootstrap_servers:
    - !ENV ${BOOTSTRAP_SERVER}
  security_protocol: "SSL"
  ssl_cafile: !ENV ${CA_FILE}
  ssl_certfile: !ENV ${CERT_FILE}
  ssl_keyfile: !ENV ${KEY_FILE}
  group_id: healthcheck-cloud-group
  auto_offset_reset: earliest
  topics:
    - source_topic: healthcheck-topic-cloud-providers
      connection_uri: !ENV ${POSTGRES_CONNECTION_URI}
      table_name: HealthCheck
    - source_topic: healthcheck-topic-cloud-providers
      connection_uri: !ENV ${POSTGRES_CONNECTION_URI}
      table_name: HealthCheckReplica
```

After having configured the `config.yaml` file, you can run the producer and the consumer using the following commands:

```bash
export CA_FILE=./certificates/ca.pem
export CERT_FILE=./certificates/service.cert
export KEY_FILE=./certificates/service.key
export POSTGRES_CONNECTION_URI=postgresql://your-username:your-password@your-postgres-database:5432/your-database-name



docker run eliax1996/python-quickstart-project:16-SNAPSHOT --consumer -c config.yaml &
docker run eliax1996/python-quickstart-project:16-SNAPSHOT --producer -c config.yaml &
```

In this case, the producer and the consumer will use the external services to store the results.