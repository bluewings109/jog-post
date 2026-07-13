FROM ghcr.io/bluewings109/jog-post:latest

RUN apt-get update && apt-get install -y --no-install-recommends jq netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
