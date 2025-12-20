FROM vllm/vllm-openai:latest

WORKDIR /app

ENV HF_HOME=/root/.cache/huggingface \
    TRANSFORMERS_CACHE=/root/.cache/huggingface \
    CUDA_VISIBLE_DEVICES=0

COPY run_model.sh /app/run_model.sh

RUN chmod +x /app/run_model.sh

EXPOSE 8000

ENTRYPOINT ["/app/run_model.sh"]
