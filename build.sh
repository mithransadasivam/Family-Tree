#!/bin/bash
python manage.py collectstatic --noinput

echo "--- DB env debug ---"
echo "MYSQLHOST=$MYSQLHOST"
echo "MYSQLPORT=$MYSQLPORT"
echo "MYSQLDATABASE=$MYSQLDATABASE"
echo "MYSQLUSER=$MYSQLUSER"
echo "MYSQLPASSWORD is set: $( [ -n \"$MYSQLPASSWORD\" ] && echo yes || echo no )"
echo "DB_HOST=$DB_HOST"
echo "DB_PORT=$DB_PORT"
echo "DB_NAME=$DB_NAME"
echo "DB_USER=$DB_USER"
echo "DB_PASSWORD is set: $( [ -n \"$DB_PASSWORD\" ] && echo yes || echo no )"
echo "--------------------"

python manage.py migrate
