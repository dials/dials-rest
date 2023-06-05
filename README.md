# A RESTful API to a (limited) subset of DIALS functionality.

```
mamba env create -f environment.yml
mamba activate dials-rest
pip install -e .
```

Generate a JWT secret and store it in the `DIALS_REST_JWT_SECRET` environment variable:
```
$ export DIALS_REST_JWT_SECRET=`openssl rand -hex 32`
```

Create a new access token:
```
$ export TOKEN=`create-access-token --expiry 2023-06-01`
```

Start the app:
```
$ uvicorn dials_rest.main:app --reload
```

<!-- curl -X 'POST' 'http://127.0.0.1:8001/export_bitmap/' -H 'accept: application/json' -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2ODU1Nzc2MDB9.i6ipplAzjhfBDAZFRsw3UTXYWbQnzZ02YDUSnpvz4j0' -H 'Content-Type: application/json' -d '{ -->
In another terminal:
```
curl -X 'POST' 'http://127.0.0.1:8000/export_bitmap/' -H 'accept: application/json' -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{
  "filename": "/dls/i24/data/2022/cm31109-5/myoglobin_dithionite/myglobin_3_00001.cbf",
  "image_index": 1,
  "format": "png",
  "binning": 4,
  "display": "image",
  "colour_scheme": "greyscale",
  "brightness": 10,
  "resolution_rings": {
    "show": true,
    "number": 10
  }
}' -o image.png
```


## Docker/podman
To build with docker/podman:
```
$ podman build -t dials-rest --format=docker .
```

To create an access token:
```
$ podman run -e DIALS_REST_JWT_SECRET=$DIALS_REST_JWT_SECRET -it dials-rest /env/bin/create-access-token
```

To run the server:
```
$ podman run -e DIALS_REST_JWT_SECRET=$DIALS_REST_JWT_SECRET -p 127.0.0.1:8081:80 dials-rest
```


## Monitoring
Before starting the DIALS REST server export the environment variable `export DIALS_REST_ENABLE_METRICS=1` to enable a `/metrics` endpoint in [prometheus](https://prometheus.io/) format.

Next add a simple `prometheus.yml` config file that tells prometheus where to scrape metrics from:
```
$ cat > prometheus.yaml << EOF
scrape_configs:
  - job_name: "dials-rest"
    scrape_interval: 15s
    static_configs:
      - targets: ["localhost:8000"]
EOF
```
Run prometheus via podman (or equivalently docker) exposed on port 9091:
```
$ podman run --network=host -v $PWD/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus --web.listen-address="localhost:9091" --config.file=/etc/prometheus/prometheus.yml
```


## Unit tests
To run unit tests:
```
$ mamba install -y dials-data httpx pytest
$ pytest --regression
```
