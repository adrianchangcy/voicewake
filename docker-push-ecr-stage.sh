#this script builds vw-stage images and deploys to ECR

#at VSCode, open new Git Bash terminal
#then type: "sh thisfile.sh"

#create session
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 981060373951.dkr.ecr.us-east-1.amazonaws.com

#build all services docker-compose-stage.yaml
docker-compose --env-file ./env/.env --file docker-compose-stage.yaml up -d --no-deps --force-recreate --no-start --build

#tag freshly built images with ECR tags
docker tag vw_stage-django_celery_beat:latest 981060373951.dkr.ecr.us-east-1.amazonaws.com/vw_stage_django_celery_beat:latest
docker tag vw_stage-django_celery_worker:latest 981060373951.dkr.ecr.us-east-1.amazonaws.com/vw_stage_django_celery_worker:latest
docker tag vw_stage-django_gunicorn:latest 981060373951.dkr.ecr.us-east-1.amazonaws.com/vw_stage_django_gunicorn:latest
docker tag vw_stage-nginx:latest 981060373951.dkr.ecr.us-east-1.amazonaws.com/vw_stage_nginx:latest

#push to AWS ECR
docker push 981060373951.dkr.ecr.us-east-1.amazonaws.com/vw_stage_django_celery_beat:latest
docker push 981060373951.dkr.ecr.us-east-1.amazonaws.com/vw_stage_django_celery_worker:latest
docker push 981060373951.dkr.ecr.us-east-1.amazonaws.com/vw_stage_django_gunicorn:latest
docker push 981060373951.dkr.ecr.us-east-1.amazonaws.com/vw_stage_nginx:latest