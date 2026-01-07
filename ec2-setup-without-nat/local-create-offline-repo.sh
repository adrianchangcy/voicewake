#step 1, prepare container
    #local machine with internet, run container by pulling from amazonlinux:latest, install packages there
        #at /docker-compose-dev.yaml
            #name: um
                #services:
                    #aws_linux:
                    #    image: amazonlinux:latest
                    #    tty: true
                    #    ports:
                    #    - "6677:6677"
                    # volumes:
                    # - type: bind
                    #     source: ./ec2-setup/local-create-offline-repo.sh
                    #     target: /local-create-offline-repo.sh
    #build container
        #docker-compose --env-file ./env/.env --file ./docker-compose-dev.yaml up -d  --build aws_linux

#step 2a, inside container, preparing packages and folder
dnf update -y;
dnf install -y dnf-plugins-core;
dnf install -y createrepo_c tar;
dnf install -y wget;
rm -f offline_repo;
    #remove any older versions of folder just for script resilience
mkdir -p offline_repo/pkgs;
    #-p means create both parent folder and subfolder

#step 2b, download packages into repo without installing at host
#docker+postgresql
dnf download --resolve --alldeps --forcearch=aarch64 --destdir=offline_repo/pkgs \
    docker \
    postgresql17 \
    postgresql17-server;
#pgbackrest dependencies
dnf download --resolve --alldeps --forcearch=aarch64 --destdir=offline_repo/pkgs \
    postgresql-libs libssh2;
#meson + ninja-build + build dependencies
dnf download --resolve --alldeps --forcearch=aarch64 --destdir=offline_repo/pkgs \
    meson ninja-build \
    postgresql17-devel \
    gcc openssl-devel libxml2-devel lz4-devel libzstd-devel bzip2-devel libyaml-devel libssh2-devel;
    #run "arch" command as-is, to check if your system is x86_64 or arm64
    #--forcearch: arm64 tends to be cheaper on AWS (t4g), which is called "aarch64" here
    #if you get OpenSSL errors here, especially "decryption failed or bad record mac", turn airplane mode off/on and rerun command
    #ninja is "ninja-build" in AWS Linux 2023

#step 2c, creating repo of our packages then compressing
createrepo_c offline_repo/pkgs;
tar -czvf offline_repo.tar.gz ./offline_repo/;
    #createrepo_c crucially generates repodata for package managers so they don't need internet, a.k.a. "air-gapped systems"
    #-czvf: -c is create, -z is gzip, -v is verbose, -f is name of tar in next arg
ls -lh offline_repo.tar.gz
    #list (ls) file in -l (long format) and -h (human-readable)

#step 2d, download pgbackrest
    #does not have separate x86_64 and aarch64 installation
wget -O pgbackrest.tar.gz https://github.com/pgbackrest/pgbackrest/archive/release/2.57.0.tar.gz
    #-O (oh) is output directory
    #for older versions, you will have /.configure, use "make" to install
    #for newer versions, you have meson.build, use meson+ninja to install

#step 2e, download docker compose plugin
    #open "https://github.com/docker/compose/releases" > scroll to "assets" > choose correct asset > copy link and paste here
wget -O docker-compose https://github.com/docker/compose/releases/download/v5.0.1/docker-compose-linux-aarch64

#step 3, export all .tar.gz and executables from within container to host machine
    #at host machine cmd
        #docker ps
        #docker cp vw_dev-aws_linux-1:offline_repo.tar.gz ./ec2-setup-without-nat/
        #docker cp vw_dev-aws_linux-1:pgbackrest.tar.gz ./ec2-setup-without-nat/
        #docker cp vw_dev-aws_linux-1:docker-compose ./ec2-setup-without-nat/

#step 4, manually upload to S3
    #at host machine > right-click the .tar.gz > reveal in file explorer > drag-and-drop into S3 bucket



#==============NOTES==============

#step 2 notes
    #-y means "yes" to all prompts
    #if you multiline your command for better readability via "\", last line should not have "\"
    #"dnf download", from dnf-plugins-core, is same as "dnf install --downloadonly"
    #createrepo_c is the modern successor of createrepo
    #use native systemd timers for pgbackrest cronjobs, instead of cronjob packages
        #cronjob packages for AWSLinux2023 are planned to be deprecated
        #https://docs.aws.amazon.com/linux/al2023/ug/deprecated-al2023.html#deprecated-cron
    #for list of available packages in AWS Linux 2023:
        #https://docs.aws.amazon.com/linux/al2023/release-notes/all-packages-AL2023.9.html
    #meson + ninja are frequently used together
        #in aws linux 2023, ninja package is renamed as ninja-build

#=================================