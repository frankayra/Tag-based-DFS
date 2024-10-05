docker network create ds_network
docker run -it --name server1 -d --network ds_network ds-server
docker exec -it server1 /bin/bash

@REM docker run -it --name server2 -d --network ds_network ds-server