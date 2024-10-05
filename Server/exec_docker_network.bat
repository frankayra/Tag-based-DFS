@REM docker network create ds_network
@REM docker run -it --name server1 -d --network ds_network ds-server
@REM docker exec -it server1 /bin/bash
@REM docker run -it --name server2 -d --network ds_network ds-server






@REM EJECUTAR ESTO EN EL DIRECTORIO RAIZ
docker-compose up --build --scale ds-server=2

@REM EJECUTAR ESTO EN CADA UNA DE LAS CONSOLAS PARA SEPARAR LOS LOGS
docker-compose logs -f nombre_del_servicio