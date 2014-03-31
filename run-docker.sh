# Make a persistent(-ish) cache volume
docker build -t oacensus/cache - < Dockerfile-cache
docker ps -a | grep OACENSUSCACHE || docker run --name=OACENSUSCACHE oacensus/cache

docker build -t oacensus/development .
docker run -t -i --volumes-from=OACENSUSCACHE -v ~/dev/oacensus:/home/oacensus/oacensus oacensus/development /bin/bash

# The first time you use this container, you'll need to:
# sudo chown -R oacensus /home/oacensus
