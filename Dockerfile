FROM       ubuntu
MAINTAINER Ana Nelson <ana@ananelson.com>

# Use squid deb proxy to cache ubuntu installs as per https://gist.github.com/dergachev/8441335
# Comment this line out if squid-deb-proxy not configured on host.
RUN /sbin/ip route | awk '/default/ { print "Acquire::http::Proxy \"http://"$3":8000\";" }' > /etc/apt/apt.conf.d/30proxy

RUN apt-get update

RUN apt-get install -y python-dev
RUN apt-get install -y python-pip

RUN apt-get install -y python-scipy
RUN apt-get install -y python-numpy
RUN apt-get install -y python-matplotlib

# Dependencies for lxml
RUN apt-get install -y libxml2-dev
RUN apt-get install -y libxslt1-dev
RUN pip install cython

RUN pip install lxml

# So we can run tests
RUN pip install nose

#ADD . /home/oacensus/oacensus
#RUN cd /home/oacensus/oacensus && pip install -e .

# Create a user
RUN useradd -m -p $(perl -e'print crypt("foobarbaz", "aa")') oacensus
RUN adduser oacensus sudo

# Fix permissions because we copied files using ADD
#RUN chown -R oacensus /home/oacensus

# Run as new user
USER oacensus

ENV HOME /home/oacensus
#RUN oacensus help
#RUN cd /home/oacensus/oacensus && nosetests
