FROM python AS dev

RUN pip3 install poetry

WORKDIR /app

COPY pyproject.toml .

RUN poetry install --no-interaction
RUN poetry export --no-interaction --without-hashes --format requirements.txt --output requirements.txt

COPY main.py .

ENTRYPOINT ["poetry", "run", "functions-framework", "--target", "youtube_transcript_api", "--debug"]

FROM google/cloud-sdk AS deploy

WORKDIR /app
COPY --from=dev /app/main.py .
COPY --from=dev /app/requirements.txt .

