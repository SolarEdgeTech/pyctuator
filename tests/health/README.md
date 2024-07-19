# Running help-provider tests
By default, the health-provider tests are skipped unless the monitoried systems are runnign and are configured.

In order to run all the tests health-provider tests at once, you'll need to start and configure MySQL and Redis servers.

The easiest way to do so, is using docker-compose to run the advanced-example.

1. Start MySQL and Redis - from the `example/Advanced` folder, run:
   ```
   docker-compose --project-name example --file docker-compose.yml up --force-recreate
   ```
1. Run the tests - from the `tests/health` folder, run:
   ```
   TEST_MYSQL_SERVER=localhost TEST_REDIS_SERVER=localhost poetry run pytest
   ```