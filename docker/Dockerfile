### "base"
FROM       phusion/baseimage
MAINTAINER Ana Nelson <ana@ananelson.com>

### "locale"
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8

### "squid-deb-proxy"
# Use squid deb proxy (if available on host OS) as per https://gist.github.com/dergachev/8441335
# Modified by @ananelson to detect squid on host OS and only enable itself if found.
ENV HOST_IP_FILE /tmp/host-ip.txt
RUN /sbin/ip route | awk '/default/ { print "http://"$3":8000" }' > $HOST_IP_FILE
RUN HOST_IP=`cat $HOST_IP_FILE` && curl -s $HOST_IP | grep squid && echo "found squid" && echo "Acquire::http::Proxy \"$HOST_IP\";" > /etc/apt/apt.conf.d/30proxy || echo "no squid"

### "apt-defaults"
RUN echo "APT::Get::Assume-Yes true;" >> /etc/apt/apt.conf.d/80custom
RUN echo "APT::Get::Quiet true;" >> /etc/apt/apt.conf.d/80custom

### "update"
RUN apt-get update
RUN apt-get install software-properties-common
RUN apt-get install build-essential

### "utilities"
RUN apt-get install sudo vim ack-grep

### "libraries"
RUN apt-get install zlib1g-dev
RUN apt-get install libffi-dev
RUN apt-get install libssl-dev

### "python"
RUN apt-get install python-dev
RUN apt-get install python-pip

### "lxml"
RUN apt-get install libxml2-dev
RUN apt-get install libxslt1-dev
RUN pip install cython

RUN pip install lxml

### "scipy"
RUN apt-get install python-scipy
RUN apt-get install python-numpy
RUN apt-get install python-matplotlib

### "python-dev-utils"
RUN pip install nose
RUN pip install pyflakes

### "asciidoctor"
RUN apt-get install ruby1.9.1
RUN apt-get install ruby1.9.1-dev
RUN gem install asciidoctor
RUN gem install pygments.rb

### "dexy"
RUN pip install dexy

### "create-user"
RUN useradd -m oacensus
RUN echo "oacensus:foobarbaz" | chpasswd
RUN adduser oacensus sudo

### "activate-user"
ENV HOME /home/oacensus
USER oacensus
WORKDIR /home/oacensus
