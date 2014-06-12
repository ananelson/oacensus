### "make-container"
docker build -t oacensus/development . && \
    docker run -t -i \
    -v `pwd`/..:/home/oacensus/oacensus \
    oacensus/development /bin/bash
