#!/bin/bash
    #run this file as bash

#=========HOW TO EXECUTE THIS SCRIPT=========
    #copy from S3 to host, give it executable permission, ensure vars passed is correct, and run
        #sudo aws s3 cp s3://voicewake-bucket/ec2-setup-without-nat/live-ec2-setup.sh ./live-ec2-setup.sh;
        #sudo chmod -x ./live-ec2-setup.sh;
        #STAGE_OR_PROD="stage" sh ./live-ec2-setup.sh;
#============================================

#=========PREREQUISITES=========
#1, prepare repo from online machine for offline installation
    #refer to ./local-create-offline-repo.sh

#2, prepare VPC interface endpoint for ECR
    #only turn on when needing ecr pull, then delete when done
        #else 7.3usd per AZ per month
            #https://aws.amazon.com/privatelink/pricing/
    #steps
        #VPC > endpoints > create endpoint > type (AWS services), services (com.amazonaws.us-east-1.ecr.api), subnets (select only 1 private subnet)
        #VPC > endpoints > create endpoint > type (AWS services), services (com.amazonaws.us-east-1.ecr.dkr), subnets (select only 1 private subnet)
    #notes
        #you only have to stop here, no configuring Security Group or Route Table needed
        #.dkr means Docker
#===============================

if [[ "${STAGE_OR_PROD}" != "stage" && "${STAGE_OR_PROD}" != "prod" ]]; then
    echo "STAGE_OR_PROD is not stage/prod.";
    exit 1;
fi;

#ECS + RDS is easier by a ton to set up
    #no manual package management, auto env var management by specifying .env at S3, etc.
#doing EC2 for everything in hopes of cost saving, since it's 0 users

#import from S3
    #if you get hanging network here, do Ctrl+C and rerun with "--debug" flag for potential clues
    #it took a few minutes for the correct network settings, to go successful "aws s3 ls" and failing "aws s3 cp", to fully successful
    #easier to do singular .env for entire machine
sudo aws s3 cp "s3://voicewake-bucket/${STAGE_OR_PROD}.env" "./.env";
sudo aws s3 cp s3://voicewake-bucket/ec2-setup-without-nat/live-ec2-docker-compose.yaml ./live-ec2-docker-compose.yaml;
sudo aws s3 cp s3://voicewake-bucket/ec2-setup-without-nat/offline_repo.tar.gz ./offline_repo.tar.gz;
sudo aws s3 cp s3://voicewake-bucket/ec2-setup-without-nat/pgbackrest.tar.gz ./pgbackrest.tar.gz;
sudo aws s3 cp s3://voicewake-bucket/ec2-setup-without-nat/docker-compose /usr/libexec/docker/cli-plugins/docker-compose;

#add docker-compose as docker plugin (officially recommended)
    #you will be using it via "docker compose", not "docker-compose" anymore
sudo chmod +x /usr/libexec/docker/cli-plugins/docker-compose;

#prepare env vars to automate the rest of the script
export CURRENT_ENV=$(awk -F '=' '$1 == "CURRENT_ENV" {print $2}' .env);
export DB_NAME=$(awk -F '=' '$1 == "DB_NAME" {print $2}' .env);
export DB_PASSWORD=$(awk -F '=' '$1 == "DB_PASSWORD" {print $2}' .env);
export AWS_S3_ACCESS_KEY_ID=$(awk -F '=' '$1 == "AWS_S3_ACCESS_KEY_ID" {print $2}' .env);
export AWS_S3_SECRET_ACCESS_KEY=$(awk -F '=' '$1 == "AWS_S3_SECRET_ACCESS_KEY" {print $2}' .env);
export AWS_S3_REGION_NAME=$(awk -F '=' '$1 == "AWS_S3_REGION_NAME" {print $2}' .env);
export AWS_S3_MAIN_BUCKET_NAME=$(awk -F '=' '$1 == "AWS_S3_MAIN_BUCKET_NAME" {print $2}' .env);
    #$() is command substitution, i.e. run command then output back using print
    #-F '=' means to use '=' as separator for "value after ="
        #seems to respect nextline
    #$1 == "ENV_VAR" is an expression, i.e. actual is_equal

#make directory
sudo mkdir -p /opt/offline_repo;

#unpack into /opt, i.e. "optional", a conventional folder for storing software that is not part of core OS, to separate from /usr and /bin
    #for tar:
        #x for extract
        #z for gnuzip
        #v for verbose
        #f for file, should come at last just before file name
        #-C is change directory, i.e. unpack to specified destination
sudo tar -xzvf offline_repo.tar.gz -C /opt;

#create local .repo and replace its content
    #replace instead of adding, so repeated commands still succeed
    #piping echo to "tee" is a solution to "cat > file_path << EOF" not working even with sudo
sudo touch /etc/yum.repos.d/offline.repo;
echo "
[offline]
name=Offline Repo
baseurl=file:///opt/offline_repo/pkgs
enabled=1
gpgcheck=0
" | sudo tee /etc/yum.repos.d/offline.repo;

#preventative measure to allow installation to be successful
#by removing any stale locks, which shows error "waiting for process pid xxxx to finish"

#check (if stale lock, will say "no such process"):
    #cat /var/run/dnf.pid
    #ps -p $(cat /var/run/dnf.pid)

#fix (using semicolon so you can copy and run entire block, as && exits on first failure)
sudo killall dnf rpm;
sudo rm -f /var/run/dnf.pid;
sudo rm -f /var/cache/dnf/*lock*;
sudo rm -f /var/lib/rpm/.rpm.lock;
sudo rpm --rebuilddb;
sudo dnf clean all;

#install packages, use offline mode only at current line
    #-v is verbose
    #if you have more packages, just continue, e.g. install docker mypackage1 mypackage2 -v
#docker + postgresql
sudo dnf --disablerepo="*" --enablerepo="offline" install \
    docker \
    postgresql17 \
    postgresql17-server \
    -y -v;
#pgbackrest dependencies
sudo dnf --disablerepo="*" --enablerepo="offline" install \
    postgresql-libs libssh2 \
    -y -v;
#meson + ninja-build + build dependencies
sudo dnf --disablerepo="*" --enablerepo="offline" install \
    meson ninja-build \
    postgresql17-devel \
    postgresql-libs libssh2 \
    gcc openssl-devel libxml2-devel lz4-devel libzstd-devel bzip2-devel libyaml-devel libssh2-devel \
    -y -v;

#================================
#========POSTGRESQL SETUP========
#================================

#set up psql directories if first time
    #do this early to have file path ready for pgbackrest
    #setup will fail if it already exists
sudo postgresql-setup --initdb;

#enable auto-start next time, then start
sudo systemctl enable postgresql;
sudo systemctl start postgresql;

#replace files for psql, restart
    #workflow
        #if first time setting up EC2:
            #modify these files in EC2 using vi > copy out to S3 > paste to local git repo
        #on change:
            #change here at local git repo > paste back into S3 > copy at EC2
    #IP context:
        #private reserved IPs defined by RFC1918 is "172.16.0.0 to 172.31.255.255", a.k.a. "172.16.0.0/12"
        #default docker0 interface is 172.16.0.0/16, so after first IP, the IP to get to host is 172.16.0.1
        #IP range of containers are not guaranteed, as it draws from full private reserved IPs, so do "172.16.0.0/12" to cover container IPs
    #for first time, use vi (guide at foot of this file) to edit manually inside EC2:
        #sudo vi /var/lib/pgsql/data/postgresql.conf
            #modify (remember to unhash):
                #listen_addresses = '*'
                #archive_mode = on
                #archive_command = 'pgbackrest --stanza=main archive-push %p'
                #wal_level = replica
                #max_wal_senders = 3
                #hot_standby = on
        #sudo vi /var/lib/pgsql/data/pg_hba.conf
            #modify:
                # IPv4 local connections:
                #host    all             all             172.16.0.0/12            md5
            #remove:
                # IPv6 local connections:
                #host    all             all             ::/0                 md5
    #to copy out from EC2 to S3, so future new EC2s can just copy back in:
        #sudo aws s3 cp /var/lib/pgsql/data/postgresql.conf s3://voicewake-bucket/ec2-setup-without-nat/postgresql.conf
        #sudo aws s3 cp /var/lib/pgsql/data/pg_hba.conf s3://voicewake-bucket/ec2-setup-without-nat/pg_hba.conf
sudo aws s3 cp s3://voicewake-bucket/ec2-setup-without-nat/postgresql.conf /var/lib/pgsql/data/postgresql.conf;
sudo aws s3 cp s3://voicewake-bucket/ec2-setup-without-nat/pg_hba.conf /var/lib/pgsql/data/pg_hba.conf;

#restart to apply changes
sudo systemctl restart postgresql;

#set up superuser for postgres, use it to run psql commands
#edit password in psql, create db, add all roles to default user in db
echo ${DB_PASSWORD} | sudo passwd postgres --stdin;
sudo -u postgres -- psql -c "ALTER USER postgres WITH PASSWORD '${DB_PASSWORD}';";
sudo -u postgres -- psql -c "CREATE DATABASE ${DB_NAME};";
sudo -u postgres -- psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO postgres;";
    #"sudo su - postgres"
        #"su" is an executable
        #"s" is to invoke login shell session as that user
        #"u" is user
        #"-" is to switch to that user's own env vars, without preserving current env vars in new session
    #"sudo -u postgres"
        #"-u" is an executable
        #different from "su", directly executes commands as that user without new login session
        #use current session's env vars to interpolate as the string is defined, before it's executed
    #"--"
        #stop processing any options/flags beyond it
        #i.e. the "-c" above is not an additional option to "-u"

#check if postgresql.conf is applied to db
sudo -u postgres -- psql -c "
    show listen_addresses;
    show wal_level;
    show archive_mode;
    show archive_command;
    show max_wal_senders;
    show hot_standby;
";

#check
sudo systemctl status postgres;

#================================
#========POSTGRESQL END==========
#================================



#==================================
#========PGBACKREST SETUP==========
#==================================

#install pgbackrest
sudo mkdir -p /build && \
sudo tar -xzvf pgbackrest.tar.gz -C /build && \
sudo meson setup /build/pgbackrest /build/pgbackrest-release-2.57.0 && \
sudo ninja -C /build/pgbackrest && \
sudo cp /build/pgbackrest/src/pgbackrest /usr/bin;
    #meson will set up files for ninja to build at /build/pgbackrest
    #"pgbackrest-release-2.57.0" is original extracted directory name
    #meson + ninja is the intended convention
    #https://pgbackrest.org/user-guide-rhel.html#build

#prepare pgbackrest directories and permissions
#configuration directories
sudo chmod 755 /usr/bin/pgbackrest;
sudo mkdir -p -m 770 /var/log/pgbackrest;
sudo chown postgres:postgres /var/log/pgbackrest;
sudo mkdir -p /etc/pgbackrest;
sudo mkdir -p /etc/pgbackrest/conf.d;
sudo touch /etc/pgbackrest/pgbackrest.conf;
sudo chmod 640 /etc/pgbackrest/pgbackrest.conf;
sudo chown postgres:postgres /etc/pgbackrest/pgbackrest.conf;
#backup repository
sudo mkdir -p /var/lib/pgbackrest;
sudo chmod 750 /var/lib/pgbackrest;
sudo chown postgres:postgres /var/lib/pgbackrest;
#logs
sudo mkdir -p /var/log/pgbackrest;
sudo chmod 750 /var/log/pgbackrest;
sudo chown postgres:postgres /var/log/pgbackrest;
#tmp
sudo mkdir -p /tmp/pgbackrest;
sudo chmod 750 /tmp/pgbackrest;
sudo chown postgres:postgres /tmp/pgbackrest;

#prepare pgbackrest stanza, so it knows where our directories are
    #concepts
        #write-ahead log (WAL): crucial record of transactions made in db, enables PITR, and fills in for corrupted backups
        #continuous archiving: postgres continuously pushes its WAL for archiving
        #point-in-time recovery (PITR): uses WAL to precisely recover db from x specific time
        #incremental backup: backup only changes from last inc backup, and 1 inc backup being corrupted with no WAL means data permanently gone
        #differential backup: backup only changes from last full backup, so size is increasingly large until next full backup
    #process
        #full backup on django migration > cron full backup + cron partial backup > expire old full backups + relevant WAL
        #postgres itself decides when WAL is ready, and will call the WAL backup via postgresql.conf archive_mode + archive_command
    #key-vals
        #pg1-path: is psql data directory, i.e. "Environment=PGDATA=" in "sudo systemctl cat postgresql"
        #repo1-path: is the path in S3 bucket, has no relation to host machine directory
        #[main]/[global]: any name you choose for commands to reference later
        #repo1-retention-full: expires older full backups so only latest x amount can exist
        #repo1-retention-diff: expires older diff backups so only latest x amount can exist
        #start-fast: tells pgsql to start backup immediately without waiting for next checkpoint
echo "
[${CURRENT_ENV}]
pg1-path=/var/lib/pgsql/data
[global]
repo1-type=s3
repo1-path=/pgbackrest_output
repo1-s3-bucket=${AWS_S3_MAIN_BUCKET_NAME}
repo1-s3-endpoint=s3.amazonaws.com
repo1-s3-region=${AWS_S3_REGION_NAME}
repo1-s3-key=${AWS_S3_ACCESS_KEY_ID}
repo1-s3-key-secret=${AWS_S3_SECRET_ACCESS_KEY}
repo1-retention-full=2
repo1-retention-diff=1
start-fast=y
" | sudo tee /etc/pgbackrest/pgbackrest.conf;

#apply changes to postgresql.conf that requires any env vars
    #apply to variables with/without "#" for better flexibility
sudo awk -i inplace \
    -v key="archive_command" \
    -v value="'pgbackrest --stanza=${CURRENT_ENV} archive-push %p'" \
    'BEGINFILE {updated=0} $1 == key {print key "=" value; updated=1; next} {print} ENDFILE {}' \
    /var/lib/pgsql/data/postgresql.conf;
    #-i inplace means edit file in place
    #-v is awk vars
    #BEGINFILE {updated=0} resets flag when each file is processed
    #on $1==key match, insert new key-var via print, goes to next line
    #{print} inserts unmodified lines as-is

#apply changes so pgbackrest can access archive_command in postgresql.conf
sudo systemctl restart postgresql;

#let pgbackrest prepare files at S3, based on repo1-path
sudo -u postgres pgbackrest stanza-create --stanza="${CURRENT_ENV}" --log-level-console=info;

#check if pgbackrest is ok
    #when it warns "FileMissingError" about archive.info, it 
sudo -u postgres pgbackrest check --stanza="${CURRENT_ENV}" --log-level-console=info;

#==================================
#=========PGBACKREST END===========
#==================================



#============================
#========DOCKER SETUP========
#============================

#be sure you have VPC endpoints created for ecr.dkr + ecr.api
    #these don't need routing at security group's inbound/outbound rules

#enable auto-start next time, then start
sudo systemctl enable docker;
sudo systemctl start docker;

#log in to ECR
    #these are in .env
    #env vars only persist at current terminal session, so only for current Instance Connect
    #one-liner makes it easy to manually copy & paste
    #docker login must be performed with sudo, otherwise it will only warn "authentication token expired"
export AWS_ECR_REGION_NAME=us-east-1 && export AWS_ECR_ACCOUNT_ID=981060373951;
aws ecr get-login-password --region "${AWS_ECR_REGION_NAME}" \
    | sudo docker login -u AWS --password-stdin "${AWS_ECR_ACCOUNT_ID}.dkr.ecr.${AWS_ECR_REGION_NAME}.amazonaws.com";

#pull from ECR (will not repull if images are identical)
    #remember to exclude .env inside .dockerfile build step, else it persists in container
    #containers also cannot access env vars at host machine
    #use --env-file to pass env vars in instead
sudo docker compose --file ./live-ec2-docker-compose.yaml --env-file ./.env pull;

#start docker
    #-d for detached, i.e. current terminal not occupied by docker
        #if running without this, press d to manually detach
        #not using this can show errors better
    #up SERVICE_NAME to run only that service
    #--no-deps to ignore "depends" from yaml
sudo docker compose --file ./live-ec2-docker-compose.yaml --env-file ./.env up -d;

#run first full backup after django migrations from gunicorn container
    #do cronjob for full backup less frequently, i.e. --type=full
    #do cronjob for partial backup more frequently, i.e. --type=incr
sudo -u postgres pgbackrest --stanza=${CURRENT_ENV} backup --type=full;
sudo -u postgres pgbackrest --stanza=${CURRENT_ENV} backup --type=incr;

#make sure postgresql listens to port meant for host machine in default docker0 interface
    #docker0 is default Docker interface created
        #after x.x.x.0, first usable IP x.x.x.1 is the one to reach host machine from within container
        #default interface's IP to host machine will be 172.17.0.1
    #for "ss", expect 172.17.0.1:5432 or 0.0.0.0:5432 or [::]:5432
        #127.0.0.1:5432 alone is not enough
        #0.0.0.0 is fine, pg_hba.conf will dictate which IP is allowed
ip addr show docker0;
sudo ss -tulpn | grep postgres;

#============================
#=========DOCKER END=========
#============================


#==============================================
#=========CRONJOBS USING SYSTEMD SETUP=========
#==============================================

#explanation:
    #3 file types:
        #.service, describes work to do
        #.timer, when to run the work
        #.slice, dictates resource limits
    #why this over crontab
        #more features, can specify resource limits, more flexible, better debugging due to logs
        #AWS Linux 2023 discourages crontab, and insists on using systemd timers

#cronjob for full pgbackrest backup
#service
echo "
[Unit]
Description=Runs pgbackrest with full backup
Wants=db-backup-full.timer
[Service]
ExecStart=sudo -u postgres pgbackrest --stanza=${CURRENT_ENV} backup --type=full
WorkingDirectory=~
Slice=db-backup-full.slice
[Install]
WantedBy=multi-user.target
" | sudo tee /etc/systemd/system/db-backup-full.service;
#timer, every week
echo "
[Unit]
Description=Run db-backup-full.service every week
Requires=db-backup-full.service
[Timer]
Unit=db-backup-full.service
OnUnitInactiveSec=604800s
RandomizedDelaySec=0s
AccuracySec=1s
[Install]
WantedBy=timers.target
" | sudo tee /etc/systemd/system/db-backup-full.timer;
#slice
echo "
[Unit]
Description=Limited db-backup-full slice
DefaultDependencies=no
Before=slices.target
[Slice]
CPUQuota=10%
MemoryLimit=200M
" | sudo tee /etc/systemd/system/db-backup-full.slice;

#cronjob for differential pgbackrest backup
#service
echo "
[Unit]
Description=Runs pgbackrest with incr backup
Wants=db-backup-incr.timer
[Service]
ExecStart=sudo -u postgres pgbackrest --stanza=${CURRENT_ENV} backup --type=incr
WorkingDirectory=~
Slice=db-backup-incr.slice
[Install]
WantedBy=multi-user.target
" | sudo tee /etc/systemd/system/db-backup-incr.service;
#timer, every day
echo "
[Unit]
Description=Run db-backup-incr.service every day
Requires=db-backup-incr.service
[Timer]
Unit=db-backup-incr.service
OnUnitInactiveSec=86400s
RandomizedDelaySec=0s
AccuracySec=1s
[Install]
WantedBy=timers.target
" | sudo tee /etc/systemd/system/db-backup-incr.timer;
#slice
echo "
[Unit]
Description=Limited db-backup-incr slice
DefaultDependencies=no
Before=slices.target
[Slice]
CPUQuota=10%
MemoryLimit=200M
" | sudo tee /etc/systemd/system/db-backup-incr.slice;

#restart systemd
    #does not restart other main services like docker, unless systemd detects related changes
sudo systemctl stop db-backup-full db-backup-incr;
sudo systemctl daemon-reload;
sudo systemctl enable db-backup-full.timer db-backup-incr.timer;
sudo systemctl start db-backup-full db-backup-incr;

#useful commands
#systemctl start SERVICE
#systemctl stop SERVICE
#systemctl status SERVICE
#systemctl list-timers  # view the status of the timers
#journalctl  # view the full systemd logs in less
#journalctl -u SERVICE  # view the logs for a specific service
#journalctl -f  # tail the logs
#journalctl -f -u SERVICE  # tail the logs for a specific service

#==============================================
#==========CRONJOBS USING SYSTEMD END==========
#==============================================






#sources:
    #setting up pgbackrest
        #https://bootvar.com/guide-to-setup-pgbackrest/
            #this page is missing stanza-create
        #https://pgbackrest.org/configuration.html
    #setting up systemd timers
        #https://medium.com/horrible-hacks/using-systemd-as-a-better-cron-a4023eea996d
        #https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html


#tooltips:

    #use vi (visual editor) to edit files manually
        #press "i" to start inserting/editing, ESC to exit
        #press ":x" to save and quit, or ":q!" to quit without saving
        #press "/" to search, ESC to exit

    #kill specific container
        #sudo docker ps
        #sudo docker kill CONTAINER_ID

    #kill all containers
        #sudo docker ps -q | xargs -r sudo docker kill
            #for every container ID piped from left, run command on the right
            #-r means "don't run if input is empty"

    #enter and exit container as root
        #sudo docker ps
        #sudo docker exec -it CONTAINER_ID_OR_NAME /bin/bash
        #exit

    #show container logs
        #sudo docker logs CONTAINER_ID_OR_NAME

    #enter and exit container by container name string match
        #sudo docker ps -aqf "name=INSERT_HERE-1$" | xargs -I CONTAINER_ID sudo docker exec -it CONTAINER_ID /bin/bash
        #exit
            #must have tty:true in compose.yaml for every container

    #restart docker
        #sudo systemctl restart docker

    #stop docker
        #sudo systemctl stop docker.socket; sudo systemctl stop docker.service;

    #find psql logs
        #use "ls" to list files in a folder
            #sudo ls /var/lib/pgsql/data/log/
        #default log file format is "postgresql-%a.log"
            #sudo cat /var/lib/pgsql/data/log/postgresql-Wed.log

    #delete file
        #rm -f filename.txt

    #list tables in database
        #sudo su - postgres
        #psql -c "SELECT table_name FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema');"

    #handy postgresql troubleshooting commands
        #locate folder containing postgresql.conf and pg_hba.conf
            #sudo systemctl cat postgresql
            #you should see something like: Environment=PGDATA=/var/lib/pgsql/data
            #hence /var/lib/psql/data/postgresql.conf, etc.
            #one-liner:
                #export PSQL_PGDATA_PATH=$(sudo systemctl cat postgresql | awk -F "=PGDATA=" '$1 == "Environment" {print $2}')
        #see if postgresql.conf is applied
            #sudo su - postgres
            #psql -c "SHOW listen_addresses;"
        #for psql at host machine and apps in docker containers, see if postgres listens to interface IP
            #check your Docker's /16 range
                #ip addr show docker0
            #expect 172.17.0.1:5432 or 0.0.0.0:5432, 127.0.0.1:5432 is not enough
                #sudo ss -tulpn | grep postgres
        #check postgresql's own log files
            #journalctl -u postgresql


