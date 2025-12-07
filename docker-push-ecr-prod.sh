#this script builds vw-stage images and deploys to ECR

#this script does not deliver frontend and static files to S3
#to do so:
#run dev frontend Docker container, then: vite build --emptyOutDir -- --env=prod
#run dev Django container, then: python manage.py collectstatic --settings=voicewake.settings.prod

#at VSCode, open new Git Bash terminal
#then type: "sh thisfile.sh"

#create session
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 981060373951.dkr.ecr.us-east-1.amazonaws.com

#build all services docker-compose-prod.yaml
docker-compose --env-file ./env/prod.env --file docker-compose-prod.yaml up -d --no-deps --force-recreate --no-start --build

#tag freshly built images with ECR tags
docker tag vw_prod-django_celery_beat:latest 981060373951.dkr.ecr.us-east-1.amazonaws.com/vw_prod-django_celery_beat:latest
docker tag vw_prod-django_celery_worker:latest 981060373951.dkr.ecr.us-east-1.amazonaws.com/vw_prod-django_celery_worker:latest
docker tag vw_prod-django_gunicorn:latest 981060373951.dkr.ecr.us-east-1.amazonaws.com/vw_prod-django_gunicorn:latest
docker tag vw_prod-nginx:latest 981060373951.dkr.ecr.us-east-1.amazonaws.com/vw_prod-nginx:latest

#push to AWS ECR
docker push 981060373951.dkr.ecr.us-east-1.amazonaws.com/vw_prod-django_celery_beat:latest
docker push 981060373951.dkr.ecr.us-east-1.amazonaws.com/vw_prod-django_celery_worker:latest
docker push 981060373951.dkr.ecr.us-east-1.amazonaws.com/vw_prod-django_gunicorn:latest
docker push 981060373951.dkr.ecr.us-east-1.amazonaws.com/vw_prod-nginx:latest