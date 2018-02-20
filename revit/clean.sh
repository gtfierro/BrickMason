#!/bin/bash
echo $1
echo $2
tr < "$1" -d '\000' | tail -n +1 > "$2"
