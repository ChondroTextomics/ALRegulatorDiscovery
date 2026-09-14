## LLM Models Used for Benchmarking

The following pre-trained LLMs were benchmarked in this project. Model weights are hosted on Hugging Face Hub and are not committed to this repository.

| Model | Variant | Hugging Face Repo | Notes |
|-------|---------|--------------------|-------|
| Qwen 4B | Instruct | [Qwen/Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)) | Quantized variant used for inference benchmarking |
| Qwen 4B | Thinking | [Qwen/Qwen3-4B-Thinking-2507](https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507)) | Quantized variant used for inference benchmarking |
| Qwen 30B | Instruct | [Qwen/Qwen3-30B-A3B-Instruct-2507-FP8](https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507-FP8) | Quantized variant used for inference benchmarking |
| Qwen 30B | Thinking | [Qwen/Qwen3-30B-A3B-Thinking-2507-FP8](https://huggingface.co/Qwen/Qwen3-30B-A3B-Thinking-2507-FP8) | Quantized variant used for inference benchmarking |
| Meta 70B | Instruct | [hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4](https://huggingface.co/hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4) | AWQ-quantized variant used for inference benchmarking |
