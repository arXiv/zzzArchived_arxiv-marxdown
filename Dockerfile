FROM arxiv/base:0.12.1

WORKDIR /opt/arxiv/

# Install MySQL.
RUN yum install -y which mysql mysql-devel
RUN yum install -y http://opensource.wandisco.com/centos/7/git/x86_64/wandisco-git-release-7-2.noarch.rpm && yum install -y git

RUN pip install -U pip pipenv uwsgi
ENV LC_ALL en_US.utf-8
ENV LANG en_US.utf-8

ARG NOCACHE=1

ADD arxiv/ /opt/arxiv/arxiv/
ADD setup.py /opt/arxiv/
RUN pipenv install /opt/arxiv/
ADD bin/start.sh /opt/arxiv/

ENV PATH "/opt/arxiv:${PATH}"

EXPOSE 8000
ENV LOGLEVEL 10

ARG SITE_NAME
ARG SITE_HUMAN_NAME
ARG VERSION
ARG SOURCE
ARG SOURCE_DIR
ARG BUILD_TIME

ENV SITE_NAME=$SITE_NAME
ENV SITE_HUMAN_NAME=$SITE_HUMAN_NAME
ENV VERSION=$VERSION
ENV SOURCE=$SOURCE
ENV SOURCE_DIR=$SOURCE_DIR
ENV SOURCE_PATH=/opt/arxiv/source/$SOURCE_DIR
ENV BUILD_TIME=$BUILD_TIME

ADD source/ /opt/arxiv/source/

ENV BUILD_PATH /opt/arxiv/build
RUN ls -la /opt/arxiv/source
RUN pipenv run python -m arxiv.marxdown.build

ENTRYPOINT ["/opt/arxiv/start.sh"]
CMD ["--http-socket", ":8000", \
     "-M", \
     "-t 3000", \
     "--manage-script-name", \
     "--processes", "8", \
     "--threads", "1", \
     "--async", "100", \
     "--ugreen", \
     "--mount", "/=arxiv.marxdown.wsgi:application", \
     "--logformat", "%(addr) %(addr) - %(user_id)|%(session_id) [%(rtime)] [%(uagent)] \"%(method) %(uri) %(proto)\" %(status) %(size) %(micros) %(ttfb)"]
