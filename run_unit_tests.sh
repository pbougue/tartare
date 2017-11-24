#!/usr/bin/env bash

case "$1" in
    --nocov) NOCOV=1
        ;;
    --*) echo "USAGE $0 [--nocov]" && exit 1
        ;;
    *) NOCOV=0
        ;;
esac

echo -e "\e[93mLooking for dupplicate tests...\e[0m"
grep "def test_" tests/ -R | cut -d':' -f2 | awk '{print $2}' | uniq -c | grep -v " 1 test_"
RESULT=$?
if [ $RESULT == 0 ] ; then
    echo -e "\e[31mDupplicate tests found, aborting.\e[0m"
    exit 1
fi

echo -e "\e[32mNo dupplicate tests found, continuing.\e[0m"

TEST_COMMAND="py.test -m \"not functional\" tests"
if [ $NOCOV == 0 ] ; then
    TEST_COMMAND="$TEST_COMMAND --cov=tartare --cov-report term-missing --cov-report xml"
fi
echo $TEST_COMMAND
export TARTARE_CONFIG_FILE=../tests/testing_settings.py

TESTS_OUTPUT=$(eval $TEST_COMMAND)
TESTS_CODE=$?
echo "$TESTS_OUTPUT"
if [ $TESTS_CODE == 0 ] ; then
    exit 0
else
    echo -e "\e[93mLooking for random network errors...\e[0m"
    echo "$TESTS_OUTPUT" | egrep -h "Connection refused|ReadTimeout"
    FOUND_CONNECTION_REFUSED=$?
    if [ $FOUND_CONNECTION_REFUSED == 0 ] ; then
        echo -e "\e[93mFound random network errors, retrying...\e[0m"
        eval $TEST_COMMAND
    else
        echo -e "\e[93mNo random network errors found, exiting.\e[0m"
        exit 2
    fi
fi
