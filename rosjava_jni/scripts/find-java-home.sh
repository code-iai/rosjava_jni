#!/bin/bash

JAVA_BINARY_PATH=$(readlink -f `which java`)

if [ -z "$JAVA_BINARY_PATH" ]; then
  echo "Java binary not found"
  exit 1
fi

JAVA_BINARY_DIR=$(dirname $JAVA_BINARY_PATH)
echo -n $JAVA_BINARY_DIR/../..

