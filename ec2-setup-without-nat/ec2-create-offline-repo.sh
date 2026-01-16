#!/bin/bash

#stop entire script on exit status 1 from any command (error)
set -e

#step 1, prepare public EC2
    #launch Amazon Linux 2023 6.12 AMI
        #assign "public" subnet that has "route table > routes" 0.0.0.0/0 destination to igw-xxx target (internet gateway)
        #choose auto-assign public IP or associate public Elastic IP
        #choose security group that lets you modify S3 and outbound to 0.0.0.0/0
        #set appropriate IAM role to EC2 AFTER EC2 has been created (couldn't find option at launch menu)
    #why not use private EC2 + NAT
        #more expensive and extra config for NAT
        #not practical if you never need NAT elsewhere, setting it up/down all the time would be annoying
    #why not pack repo at local amazonlinux:latest docker container
        #that image is not 1:1 to actual EC2's Amazon Linux 2023 6.12 AMI
            #even though you are only downloading and not installing at local container, the metadata will be inconsistent
                #you will get package conflicts or missing dependencies
        #uploading/downloading between S3 and EC2 is a lot faster than uploading to S3 from local machine



#=========HOW TO EXECUTE THIS SCRIPT=========
    #sudo aws s3 cp s3://voicewake-bucket/ec2-setup-without-nat/ec2-create-offline-repo.sh ./ec2-create-offline-repo.sh;
    #sudo chmod -x ./ec2-create-offline-repo.sh;
    #sh ./ec2-create-offline-repo.sh;
#============================================



#step 2a, prepare local packages and folder
    #not running "sudo dnf update -y", since air-gapped system cannot run it
sudo dnf install -y \
    dnf-plugins-core \
    createrepo_c tar gzip \
    wget \
    git;

#if dnf hangs via "waiting for process id to finish", this fixes it
sudo killall dnf rpm || true;
    #allow this to fail with "no process found"
sudo rm -f /var/run/dnf.pid;
sudo rm -f /var/cache/dnf/*lock*;
sudo rm -f /var/lib/rpm/.rpm.lock;
sudo rpm --rebuilddb;
sudo dnf clean all;

#step 2b, prepare offline repo folder
sudo rm -rf offline_repo;
    #remove any older versions of folder just for script resilience
sudo mkdir -p offline_repo/pkgs;
    #-p means create both parent folder and subfolder

#step 2c, download packages into repo without installing at host
    #SUGGESTION
        #if you want to guarantee 100% system clone, consider "reposync" method
    #WARNING
        #do not use --alldeps, it will download all dependencies while ignoring installed packages, leading to install conflicts later
            #some of the packages affect "ec2-instance-connect", so --allowerasing or upgrading can permanently disable SSH access
            #https://github.com/rpm-software-management/dnf/issues/1998#issuecomment-1750123304
#docker, postgresql, fail2ban
sudo dnf download --resolve --destdir=offline_repo/pkgs \
    docker \
    postgresql17 \
    postgresql17-server \
    fail2ban;
#pgbackrest dependencies
sudo dnf download --resolve --destdir=offline_repo/pkgs \
    postgresql-libs libssh2;
#meson + ninja-build + build dependencies for building
sudo dnf download --resolve --destdir=offline_repo/pkgs \
    meson ninja-build \
    postgresql17-devel \
    gcc openssl-devel libxml2-devel lz4-devel libzstd-devel bzip2-devel libyaml-devel libssh2-devel;
    #if you get OpenSSL errors here, especially "decryption failed or bad record mac", turn airplane mode off/on and rerun command
    #ninja is "ninja-build" in AWS Linux 2023
    #installation guides depending on OS
        #https://pgbackrest.org/user-guide-index.html
#dos2unix to guarantee Windows-edited file does not have hidden newlines when running "awk" command in linux
sudo dnf download --resolve --destdir=offline_repo/pkgs \
    dos2unix;

#step 2d, creating repo of our packages then compressing
sudo createrepo_c offline_repo/pkgs;
sudo tar -czvf offline_repo.tar.gz ./offline_repo/;
    #createrepo_c crucially generates repodata for package managers so they don't need internet, a.k.a. "air-gapped systems"
    #-czvf: -c is create, -z is gzip, -v is verbose, -f is name of tar in next arg

#step 2e, download pgbackrest
    #does not have separate x86_64 and aarch64 installation
sudo wget -O pgbackrest.tar.gz https://github.com/pgbackrest/pgbackrest/archive/release/2.57.0.tar.gz
    #-O (oh) is output directory
    #for older versions, you will have /.configure, use "make" to install
    #for newer versions, you have meson.build, use meson+ninja to install

#step 2f, download docker compose plugin
    #open "https://github.com/docker/compose/releases" > scroll to "assets" and click "view all"
    #choose "docker-compose-linux-x86_64" or "docker-compose-linux-aarch64"
sudo wget -O docker-compose https://github.com/docker/compose/releases/download/v5.0.1/docker-compose-linux-x86_64
# wget -O docker-compose https://github.com/docker/compose/releases/download/v5.0.1/docker-compose-linux-aarch64

#step 3, export all .tar.gz and executables from this public EC2 to S3
    #at host machine cmd (to copy all commands, Ctrl+Alt+Down at start, Shift+Right)
sudo aws s3 cp offline_repo.tar.gz s3://voicewake-bucket/ec2-setup-without-nat/;
sudo aws s3 cp pgbackrest.tar.gz s3://voicewake-bucket/ec2-setup-without-nat/;
sudo aws s3 cp docker-compose s3://voicewake-bucket/ec2-setup-without-nat/;



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