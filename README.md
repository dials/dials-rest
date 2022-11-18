A RESTful API to a (limited) subset of DIALS functionality.

```
mamba create -n dials-rest
mamba activate dials-rest
mamba install python=3.10 -y
mamba install dials uvicorn[standard] -y
pip install -e .
```