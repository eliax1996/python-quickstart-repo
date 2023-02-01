# Python Healthcheck

This project is a simple healthcheck for a set of configurable websites.
It includes two running components:

1. an Http fetcher that fetches the websites and forward the result to a Kafka topic (called in the code Healthcheck
   producer)
2. a Kafka consumer that consumes the messages from the topic and stores them one or more Postgres database tables (
   called in the code Healthcheck consumer)

## running the program

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
