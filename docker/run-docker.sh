### "oacensus-dir"
OACENSUS_DIR=~/dev/oacensus

### "make-cache"
docker build -t oacensus/cache - < Dockerfile-cache
docker ps -a | grep OACENSUSCACHE || \
    docker run --name=OACENSUSCACHE oacensus/cache

### "make-container"
docker build -t oacensus/development . && \
    docker run -t -i \
    --volumes-from=OACENSUSCACHE \
    -v $OACENSUS_DIR:/home/oacensus/oacensus \
    oacensus/development /bin/bash
