FROM ubuntu:18.04

ENV LANG=en_EN.UTF-8

RUN apt-get update \
    && apt-get install --no-install-recommends --no-install-suggests --allow-unauthenticated -y \
        gnupg \
        software-properties-common \
        ca-certificates \
        wget \
        locales \
    && localedef -i en_US -f UTF-8 en_US.UTF-8 \
    # Add the current key for package downloading - As the key changes every year at least
    # Please refer to QGIS install documentation and replace it with the latest one
    && wget -qO - https://qgis.org/downloads/qgis-2020.gpg.key | gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/qgis-archive.gpg --import \
    && gpg --export --armor F7E06F06199EF2F2 | apt-key add - \
    && echo "deb http://qgis.org/debian buster main" >> /etc/apt/sources.list.d/qgis.list \
    && add-apt-repository "deb https://qgis.org/debian `lsb_release -c -s` main"
    && apt-get update \
    && apt-get install --no-install-recommends --no-install-suggests --allow-unauthenticated -y \
        qgis \
        qgis-plugin-grass \

# install python
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.7 \
    python3-pip \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV QGIS_SERVER_LOG_STDERR 1
ENV QGIS_SERVER_LOG_LEVEL 2


# If you have multiple Dockerfile steps that use different files from your context, COPY them individually,
# rather than all at once. This will ensure that each step’s build cache is only invalidated
# (forcing the step to be re-run) if the specifically required files change.
COPY requirements.txt /home/qgis

COPY . /home/qgis
WORKDIR /home/qgis

RUN pip install --no-cache-dir -r requirements.txt




