echo "checking db connection without -d flag"
pg_isready -h ${DB_HOST} -U ${DB_USER} -p ${DB_PORT}

echo "checking db connection with -d flag"
pg_isready -h ${DB_HOST} -d ${DB_NAME} -U ${DB_USER} -p ${DB_PORT}

sleep 86400