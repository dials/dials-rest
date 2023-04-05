# Container for building the environment
FROM condaforge/mambaforge:4.9.2-5 as conda

COPY environment.yml .
RUN mamba env create -p /env --file environment.yml && conda clean -afy
COPY . /pkg
RUN conda run -p /env python -m pip install --no-deps /pkg

# Distroless for execution
FROM gcr.io/distroless/base-debian11

COPY --from=conda /env /env

CMD ["/env/bin/uvicorn", "--host", "0.0.0.0", "--port", "8080", "dials_rest.main:app"]
