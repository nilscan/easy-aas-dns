FROM bitnami/openresty:1.21

USER 0

RUN apt update
RUN apt install -y git fcgiwrap

ADD reposerver/git-http-backend reposerver/run.sh /easyaas/
ADD reposerver/index.html /easyaas/index.html
RUN mkdir -p /easyaas/logs/reposerver
RUN chown -R 1001 /easyaas \
  && chmod +x /easyaas/git-http-backend \
  && chmod +x /easyaas/run.sh \
  && touch /var/run/fcgiwrap.socket && chmod a+rw /var/run/fcgiwrap.socket

USER 1001