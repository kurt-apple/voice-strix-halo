FROM ghcr.io/kyuz0/amd-strix-halo-toolboxes:rocm-7.2

#ARG MODEL_NAME=qwen3-next
#ENV MODEL_NAME=${MODEL_NAME}

WORKDIR /app

COPY ./presets.ini ./

#RUN echo '{"default": {"url": "http://host.containers.internal:8080/v1", "api_key": "na", "extra_body": {}}}' > /app/presets.json 2>/dev/null || true

EXPOSE 8080

#CMD ["-c", "localhost:8080", "--model", "${MODEL_NAME}", "--parallel", "1"]
CMD ["-c", "localhost:8080", "--models-preset", "presets.ini", "--parallel", "4"]
