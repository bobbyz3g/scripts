#!/bin/bash
# Script to parse MySQL binary log files using mysqlbinlog command

check_mysqlbinlog() {
    if ! command -v mysqlbinlog &> /dev/null; then
        echo "Error: mysqlbinlog command not found. Please install MySQL utilities."
        exit 1
    fi
}

if [ $# -ne 1 ]; then
    echo "Usage: $0 <binlog-file>"
    echo "Example: $0 mysql-bin.000001"
    exit 1
fi

BINLOG_FILE=$1

if [ ! -f "$BINLOG_FILE" ]; then
    echo "Error: Binlog file '$BINLOG_FILE' does not exist"
    exit 1
fi

check_mysqlbinlog

mysqlbinlog --base64-output=DECODE-ROWS -v "$BINLOG_FILE" | awk '{print} /COMMIT\/\*!\*\// { for (i=1; i<=3; i++) print ""}' | less
