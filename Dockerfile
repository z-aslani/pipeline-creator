FROM python:3.8
WORKDIR /pipeline_creator

COPY . .
ENV VIRTUAL_ENV=/pipeline_creator/venv
ENV PATH="/pipeline_creator/venv/bin:$PATH"
ENV PYTHONPATH /pipeline_creator

CMD ["python", "/pipeline_creator/src/rest_api.py"]
