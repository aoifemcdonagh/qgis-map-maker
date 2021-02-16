FROM ubuntu:18.04

ENV LANG=en_EN.UTF-8

RUN apt update
RUN apt install --no-install-recommends --no-install-suggests --allow-unauthenticated -y gnupg software-properties-common ca-certificates wget locales
RUN wget -qO - https://qgis.org/downloads/qgis-2020.gpg.key | gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/qgis-archive.gpg --import
RUN chmod a+r /etc/apt/trusted.gpg.d/qgis-archive.gpg
#RUN echo "deb http://qgis.org/debian buster main" >> /etc/apt/sources.list.d/qgis.list
RUN add-apt-repository "deb https://qgis.org/debian `lsb_release -c -s` main"
RUN apt update
RUN apt install --no-install-recommends --no-install-suggests --allow-unauthenticated -y qgis qgis-plugin-grass

# install python
RUN apt update
RUN apt install -y --no-install-recommends python3.7 python3-pip python3-setuptools


# If you have multiple Dockerfile steps that use different files from your context, COPY them individually,
# rather than all at once. This will ensure that each step’s build cache is only invalidated
# (forcing the step to be re-run) if the specifically required files change.
#COPY requirements.txt /home/qgis

COPY . /home/qgis
WORKDIR /home/qgis

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3 gui.py"]


