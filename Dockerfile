FROM ubuntu:20.04
WORKDIR /workspace
RUN apt update && apt install -y python3-pip
ADD requirements.txt .
RUN python3 -m pip install -r requirements.txt
ADD public_prod public_prod
ADD static static
ADD *.py ./
