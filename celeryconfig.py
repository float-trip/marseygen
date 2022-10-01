beat_schedule = {
    "find-prompts": {"task": "tasks.find_prompts", "schedule": 60.0, "args": ()},
}

task_annotations = {
    "tasks.post_reply": {"rate_limit": "5/m"},
    "tasks.find_prompts": {"rate_limit": "1/m"},
}

task_default_queue = "api"

broker_url = ""
result_backend = ""

task_routes = {"tasks.generate_reply": {"queue": "gen"}}

worker_prefetch_multiplier = 1
