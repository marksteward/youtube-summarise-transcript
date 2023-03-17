FROM python AS dev

RUN pip3 install poetry

WORKDIR /app

COPY pyproject.toml .

RUN poetry install --no-interaction
RUN poetry export --no-interaction --without-hashes --format requirements.txt --output requirements.txt

COPY main.py .
COPY run.py .

ENV PYTHONDONTWRITEBYTECODE=1

#ENTRYPOINT ["poetry", "run", "functions-framework", "--target", "youtube_summarise_transcript", "--debug"]
CMD ["poetry", "run", "python3", "run.py", "--target", "youtube_summarise_transcript", "--debug"]

FROM google/cloud-sdk AS deploy

WORKDIR /app
COPY --from=dev /app/main.py .
COPY --from=dev /app/requirements.txt .
COPY env.prod.yaml ./env.yaml

