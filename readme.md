# Marseygen

Stable Diffusion bot with distributed inference.

# Usage

* Set up [InvokeAI](https://github.com/invoke-ai/InvokeAI) on the gen workers and activate the `ldm` environment

* Install rabbitmq and redis, add URLs to `celeryconfig.py`

* `git clone https://github.com/float-trip/marseygen`

* `pip install -r marseygen/requirements.txt`

* `mv marseygen/*.py InvokeAI && cd InvokeAI`
    * Running the gen workers from this dir circumvents some Python import issues that I don't care to figure out right now

* Start the API worker

`celery -A tasks worker -B --concurrency 1 --loglevel=INFO`

* Start a gen worker for each GPU

```sh
export CUDA_VISIBLE_DEVICES=0,
export WORKER_HOST="user@gen_worker_ip"
export WORKER_SSH_PORT="22"
export WORKER_ID="unique_id"
celery -A tasks worker -Q gen -n unique_name -B --concurrency 1 --loglevel=INFO`
```

