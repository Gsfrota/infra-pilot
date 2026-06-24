FROM python:3.12-slim

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -e .

# Default to the self-contained simulated run.
ENTRYPOINT ["infrapilot"]
CMD ["demo"]
