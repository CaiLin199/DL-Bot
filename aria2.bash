#!/bin/bash

# Run aria2 with the specified options
aria2c --enable-rpc --rpc-listen-all=true --rpc-allow-origin-all --no-cache --allow-overwrite "$@"