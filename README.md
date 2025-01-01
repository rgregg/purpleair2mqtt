# Purple Air 2 MQTT

Small process to pull data from a Purple Air air sensor and publish it to MQTT broker.

## Running with Docker Compose

The easiest way to run this program is to add it to your Docker Compose environment where you are already
have MQTT and Home Assistant running.

```yaml
services:
  mqtt:
    # existing MQTT service
  purpleair2mqtt:
    container_name: purpleair2mqtt
    image: rgregg/purpleair2mqtt:main
    restart: unless-stopped
    volumes:
      - ./purpleair2mqtt/:/app/config/
    depends_on:
      - mqtt
```


## License

This project is licensed under the [MIT License](LICENSE).