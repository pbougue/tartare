#!/usr/bin/env bash

docker build -t tartare_functional_tests .
docker build -t tartare_rust_functional_tests -f Dockerfile.rust.test --pull .
docker-compose -f docker-compose.test.yml up -d
HTTP_SERVER_ID=$(docker-compose -f docker-compose.test.yml ps -q http_download_server)
export TARTARE_HOST_IP=$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker-compose -f docker-compose.test.yml ps -q tartare_webservice))
export HTTP_SERVER_IP=$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'  $HTTP_SERVER_ID)
docker cp tests/fixtures/. $HTTP_SERVER_ID:/var/www
py.test -vv tests/functional
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
