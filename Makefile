migrate:
	docker-compose exec backend python manage.py migrate


# choco install make

# docker exec -it NAME bash

docker-compose run --rm infra-backend-1 python manage.py collectstatic --no-input