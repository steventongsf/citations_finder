FROM python
RUN mkdir /myfiles
COPY requirements.txt /myfiles/requirements.txt
WORKDIR "/root/"
RUN apt-get update; apt-get install -y enchant-2 git
RUN pip install --upgrade pip
RUN pip install -r /myfiles/requirements.txt
#ENTRYPOINT cd /root/citations_finder