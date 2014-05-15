### "base"
FROM       ubuntu:13.10
MAINTAINER Ana Nelson <ana@ananelson.com>

### "locale"
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8

### "squid-deb-proxy"
# Use squid deb proxy to cache ubuntu installs as per
# https://gist.github.com/dergachev/8441335
# Comment this out if squid-deb-proxy not configured on host.
RUN /sbin/ip route | awk '/default/ { print "Acquire::http::Proxy \"http://"$3":8000\";" }' > /etc/apt/apt.conf.d/30proxy

### "update"
RUN apt-get update
RUN apt-get install -y software-properties-common
RUN apt-get install -y build-essential

### "utilities"
RUN apt-get install -y sudo
RUN apt-get install -y vim
RUN apt-get install -y ack-grep

### "libraries"
RUN apt-get install -y zlib1g-dev
RUN apt-get install -y libffi-dev
RUN apt-get install -y libssl-dev

### "python"
RUN apt-get install -y python-dev
RUN apt-get install -y python-pip

### "lxml"
RUN apt-get install -y libxml2-dev
RUN apt-get install -y libxslt1-dev
RUN pip install cython

RUN pip install lxml

### "scipy"
RUN apt-get install -y python-scipy
RUN apt-get install -y python-numpy
RUN apt-get install -y python-matplotlib

### "python-dev-utils"
RUN pip install nose
RUN pip install pyflakes

### "asciidoctor"
RUN apt-get install -y ruby2.0-dev
RUN apt-get install -y ruby2.0
RUN gem install asciidoctor
RUN gem install pygments.rb

### "dexy"
RUN pip install dexy

### "create-user"
RUN useradd -m -p $(perl -e'print crypt("foobarbaz", "aa")') oacensus
RUN adduser oacensus sudo

### "switch-to-user"
USER oacensus
ENV HOME /home/oacensus
