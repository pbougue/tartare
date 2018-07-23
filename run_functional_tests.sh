#!/usr/bin/env bash
MARK="-m \"not regression\""
if [ $1 == "regression" ]; then
    MARK="-m \"not functional\""

fi
docker build -t tartare_functional_tests .
docker pull navitia/ruspell
docker pull navitia/navitia_model
docker build -t tartare_rust_functional_tests -f Dockerfile.rust.test .
docker-compose -f docker-compose.test.yml up -d
HTTP_SERVER_ID=$(docker-compose -f docker-compose.test.yml ps -q http_download_server)
export TARTARE_HOST_IP=$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker-compose -f docker-compose.test.yml ps -q tartare_webservice))
export HTTP_SERVER_IP=$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'  $HTTP_SERVER_ID)
docker cp tests/fixtures/. $HTTP_SERVER_ID:/var/www
TEST_COMMAND="py.test -vv $MARK tests/functional"
eval $TEST_COMMAND
RESULT=$?
if [ $RESULT -eq 0 ]; then
    echo "Tests passed"
else
    echo "/!\ Tests failed, last logs:"
    docker logs tartare_test_worker
    docker logs tartare_test_ruspell_worker
    docker logs tartare_test_gtfs2ntfs_worker
fi
docker-compose -f docker-compose.test.yml down -v
exit $RESULT
