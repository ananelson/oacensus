### "oacensus-dir"
OACENSUS_DIR=~/dev/oacensus

### "make-container"
docker build -t oacensus/development . && \
    docker run -t -i \
    -v $OACENSUS_DIR:/home/oacensus/oacensus \
    oacensus/development /bin/bash
