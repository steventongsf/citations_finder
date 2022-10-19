cwd := $(shell pwd)
build:
	docker build --progress plain -f .\Dockerfile -t mypython:latest .
run:
	docker run -it --rm --name python -v ${cwd}:/root/citations_finder mypython:latest bash

all: build run
