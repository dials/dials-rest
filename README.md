A RESTful API to a (limited) subset of DIALS functionality.

```
mamba env create -f environment.yml
mamba activate dials-rest
mamba install python=3.10 -y
mamba install dials uvicorn[standard] -y
pip install -e .
```

Generate a JWT secret and store it in the `JWT_SECRET` environment variable:
```
$ export JWT_SECRET=`openssl rand -hex 32`
```

Create a new access token:
```
$ create-access-token --expiry 2022-12-31
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2NzI0NDQ4MDB9.8J_5yadgK3UrErs1AOXKxjlvkzc-GCNA6Eg-v9obpvU
```

Start the app:
```
$ uvicorn dials_rest.main:app --reload
```

In another terminal:
```
curl -X 'GET'   'http://127.0.0.1:8000/export_bitmap/'   -H 'accept: application/json'   -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2NzI0NDQ4MDB9.8J_5yadgK3UrErs1AOXKxjlvkzc-GCNA6Eg-v9obpvU'   -H 'Content-Type: application/json'   -d '{
  "filename": "/dls/i24/data/2022/cm31109-5/myoglobin_dithionite/myglobin_3_00001.cbf",
  "image_index": 1,
  "format": "png",
  "binning": 4,
  "display": "image",
  "colour_scheme": "greyscale",
  "brightness": 10
}' > image.png
```

To build with docker/podman:
```
$ podman build -t dials-rest --format=docker .
```

To create an access token:
```
$ podman run -e JWT_SECRET=$JWT_SECRET -p 127.0.0.1:8081:80 -it dials-rest /env/bin/create-access-token
```

To run the server:
```
$ podman run -e JWT_SECRET=$JWT_SECRET -p 127.0.0.1:8081:80 -it dials-rest /env/bin/create-access-token
```
