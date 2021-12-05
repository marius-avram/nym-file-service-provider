#!/bin/bash

# sample run is:
# ./retry-nym-client.sh <your_client_id> 

until ./nym-client run --id $@; do
    echo "nym client could not connect, retrying in 2 seconds.."
    sleep 2
done
