docker run -d \
  --name vllm-qwen \
  --restart unless-stopped \
  --gpus all \
  --network host \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm-qwen
