test:
    pytest

lint:
    flake8 src

install:
    pip install -r requirements.txt


build-docker:
    docker buildx create --use
    docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 -t rgregg/purpleair2mqtt:main . --push