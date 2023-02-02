# Python Healthcheck

This project is a configurable website healthcheck tool. It consists of two components:

1. The Healthcheck Producer, implemented as an HTTP Fetcher, which retrieves website data and forwards it to a Kafka
   topic.
2. The Healthcheck Consumer, a Kafka consumer, which consumes messages from the topic and stores them in one or more
   tables in a Postgres database

## running the program locally

The ci/cd pipeline is configured to run the program in a docker container,
which is built and pushed to the `eliax1996/python-quickstart-project` docker
image.
The image is updated with each new version that is detected by the CI.
The current version is tagged as `22-SNAPSHOT`.

To run the program locally, follow these steps:

1. Clone the repository.
2. Enter the project directory.
3. Run the following command to start the Docker Compose:

```bash
docker-compose up
```

This will start the Postgres database, the Kafka broker, and the Zookeeper.

To run the Consumer locally, set the environment variables and configure the `config.yaml` file (a valid configuration
is already available in the root of the repo).
Then, run the following command to create the Consumer (the volume mounting is necessary for Docker to read the
config.yaml file while the `--network-host`
flag is necessary to allow the container to connect to the Kafka broker and the Postgres database):

```bash
export CONFIG_PATH="/absolute/path/of/python-quickstart-repo/config.yaml"

docker run -v $CONFIG_PATH:/app/config.yaml --network="host" \
           eliax1996/python-quickstart-project:21-SNAPSHOT --consumer -c config.yaml
```

And then run the following command to create the producer:

```bash

docker run -v $CONFIG_PATH:/app/config.yaml --network="host" \
           eliax1996/python-quickstart-project:21-SNAPSHOT --producer -c config.yaml
```

At this point, you have a running Consumer and Producer that will fetch websites and store the results in the database.
To view the results, connect to the Postgres database and run a query on the specified table.

Assuming the table name is `healthcheck` (the default name in the `config.yaml`), you can run the following query to see
the results:

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
An example of the configuration is the following (available in the `remote-services-config.yaml`:

```yaml
healthcheck-producer-config:
  bootstrap_servers:
    - !ENV ${KAFKA_BOOTSTRAP_SERVER}
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
    - !ENV ${KAFKA_BOOTSTRAP_SERVER}
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
# export the environment variables
export POSTGRES_CONNECTION_URI="postgres://admin:admin@postgresql:5432/healthcheck"
export KAFKA_BOOTSTRAP_SERVER="my-kafka-broker:9092"
export CONFIG_PATH="/absolute/path/to/python-quickstart-repo/remote-services-config.yaml"
export CERTIFICATE_FOLDER="/absolute/path/to/my/certificates/"
```

```bash
# launch the consumer

docker run -e POSTGRES_CONNECTION_URI=$POSTGRES_CONNECTION_URI \
           -e KAFKA_BOOTSTRAP_SERVER=$KAFKA_BOOTSTRAP_SERVER \
           -e CA_FILE=./certificates/ca.pem \
           -e CERT_FILE=./certificates/service.cert \
           -e KEY_FILE=./certificates/service.key \
           -v $CONFIG_PATH:/app/remote-services-config.yaml \
           -v $CERTIFICATE_FOLDER:/app/certificates \
           eliax1996/python-quickstart-project:22-SNAPSHOT --consumer -c remote-services-config.yaml
```

```bash
# launch the producer

docker run -e POSTGRES_CONNECTION_URI=$POSTGRES_CONNECTION_URI \
           -e KAFKA_BOOTSTRAP_SERVER=$KAFKA_BOOTSTRAP_SERVER \
           -e CA_FILE=./certificates/ca.pem \
           -e CERT_FILE=./certificates/service.cert \
           -e KEY_FILE=./certificates/service.key \
           -v $CONFIG_PATH:/app/remote-services-config.yaml \
           -v $CERTIFICATE_FOLDER:/app/certificates \
           eliax1996/python-quickstart-project:22-SNAPSHOT --producer -c remote-services-config.yaml
```

In this case, the producer and the consumer will use the external services to store the results.

# Technical Overview

The producer and consumer components are implemented using the asynchronous `aiokafka` library, which is built
on `asyncio`.
This ensures that the components can handle a large number of requests without blocking the execution.
The entire application (both for the consumer and the producer) is completely asynchronous and non-blocking.

Both the database connection and HTTP requests are also handled asynchronously,
using the `asyncpg` library for the database and the `aiohttp` library for HTTP requests.

Code quality is maintained through testing using the `pytest` library, and the CI/CD pipeline is managed
through `Github Actions`,
automatically triggered with each new commit to the repository.

The configurations are loaded with the `pyyaml` and `pyaml-env` libraries,
enabling the use of YAML-formatted files with environment variables as the configuration files.

### The database design

The database design was based on the possibility of horizontally scaling the application.
The primary key was created with this in mind, and it consists of the hash of the `url` and the `timestamp` of the
request.
This design was chosen because the hash of the `url` is unique for each website and has a fixed length, making it easy
to store and index in the database.

However, this simple design has a drawback: different subdomains of the same website have a completely different hash.
A better approach would have been to store the root domain and then to store the subdomain as a separate column,
but this was not implemented due to time constraints.

Data insertion is performed using the `INSERT ... ON CONFLICT DO UPDATE` statement.
This is necessary because Kafka is an "at least once" delivery system,
meaning that the same message may be delivered multiple times (for example, if the consumer crashes before acknowledging
receipt but after writing the message to `PostgreSQL`).
In this case, the `ON CONFLICT DO UPDATE` statement updates the row with the new values,
effectively implementing an upsert operation.

### The kafka design

Kafka Design
The messages are stored in the Kafka topic using `JSON` formatting.
The key of each message is set to the `URL`, in order to distribute the messages efficiently across the partitions
and to maintain the ordering of messages for the same URL.

## The ci/cd pipeline

The CI/CD pipeline performs the following tasks in order:

1. Verification of code style, typing, and formatting via `pre-commit` hooks (that can be configured to run also locally
   before pushing).

2. Execution of unit tests.

3. Code coverage analysis (and wall if the coverage isn't enough).

4. Creation of Docker images for various platforms using QEMU.

5. Deployment of Docker images to Docker Hub with a `github.run_number-SNAPSHOT` tag.

# Known Issues, Limitations, and Possible Improvements

1. Given the limited amount of time, basic logging was added, but observability was not fully implemented.
   To have a better understanding of the application behavior, metrics and tracing could be added in the future.

2. The current CI/CD pipeline could be improved by creating a semantic versioning system and adding a more descriptive
   Docker tag.

3. The code for loading configurations can be simplified to reduce complexity.

4. The consumer's dictionary that tells which consumer is responsible for which topic is based on a `dict`. Since
   dict in python are invariant, they didn't have a precise enough type. The workaround I've implemented is to use the
   upper type as type signature.
   The ideal solution it is to use an immutable dictionary that could be variant and enables a more precise type
   checking.

5. Currently, Only `SSL` is currently supported as a security protocol, adding support for `SASL_SSL` would be desirable.

6. The consumers and producers depend on the existence of topics. It would be useful to also manage the creation of topics.

7. The data serialization method could be improved by using a more efficient format such as Avro, with a schema registry
   to support schema evolution.

8. It would be nice to have an external service to check the writing of the data in the database, in order to have a
   better understanding of the application behaviour and find rapidly possible issues.

9. A mechanism for handling consumer and producer failures is currently missing. A scheduler could be added to automatically restart these components in case of failure.

10. While PostgreSQL is used to store data, a time-series database may be a better choice for storing measurements.

11. Monitoring database writes through an external service could provide a deeper understanding of the application's behavior and facilitate faster issue detection.