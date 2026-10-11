docker-compose -f docker-compose.yml -f letsencrypt-docker-compose.yml down

docker-compose -f docker-compose.yml -f letsencrypt-docker-compose.yml up -d --build

Start-Sleep -Seconds 30

docker-compose exec web python manage.py migrate

docker-compose exec web python manage.py collectstatic --noinput
