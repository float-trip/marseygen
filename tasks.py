import os
import subprocess
import random
from celery import Celery, Task, chain
import time
import celeryconfig

from client import DramaClient
from utils import concat_images

app = Celery("tasks")
app.config_from_object(celeryconfig)

client = DramaClient()

generator = None


#
# API worker tasks
#
@app.task
def post_reply(context):
    basename = os.path.basename(context["image_path"])
    save_path = f"/fs/marseys/{basename}"

    print(f"Copying {basename}")

    # Copy image from remote machine.
    subprocess.run(
        [
            "rsync",
            "-a",
            f"{context['worker_host']}:{context['image_path']}",
            save_path,
            "-e",
            f"ssh -p {context['worker_ssh_port']}",
        ]
    )

    print(f"Replying for prompt {context['prompt']}")

    client.reply(
        context["parent_fullname"],
        context["submission"],
        f"`{context['prompt']}`",
        save_path,
    )


class FindPromptsTask(Task):
    last_call = None

    # Temp fix for comments being replied to multiple times.
    queued_ids = set()


@app.task(base=FindPromptsTask)
def find_prompts():
    if find_prompts.last_call is not None and time.time() - find_prompts.last_call < 60:
        return

    find_prompts.last_call = time.time()

    print("Looking for prompts.")
    comments = client.fetch_new_comments()

    for comment in comments:
        if comment["id"] in find_prompts.queued_ids:
            continue

        find_prompts.queued_ids.add(comment["id"])

        reply_contexts = [
            {
                "parent_fullname": f"c_{comment['id']}",
                "submission": comment["post_id"],
                "prompt": line[4:],
            }
            for line in comment["body"].split("\n")
            if line.startswith("!sd ")
        ]

        # Max 5 prompts per comment.
        reply_contexts = reply_contexts[:5]

        for context in reply_contexts:
            print(f"Queueing prompt `{context['prompt']}`.")
            chain(
                generate_reply.s(context).set(queue="gen"),
                post_reply.s().set(queue="api"),
            ).apply_async()


#
# Generation worker tasks
#
class GenTask(Task):
    _generator = None

    @property
    def generator(self):
        if self._generator is None:
            from ldm.generate import Generate

            self._generator = Generate(sampler_name="k_euler_a")
            self._generator.load_model()

            print("Model loaded.")

        return self._generator


@app.task(base=GenTask)
def generate_reply(context):
    print(f"Generating `{context['prompt']}`.")

    if not os.path.exists("out"):
        os.makedirs("out")

    results = generate_reply.generator.prompt2png(
        context["prompt"], outdir=f"out/{os.environ['WORKER_ID']}", iterations=9
    )

    image_paths = [r[0] for r in results]
    grid = concat_images(image_paths, size=(512, 512), shape=(3, 3))

    grid_basename = f"{random.randrange(10**6, 10**7)}.webp"

    if not os.path.exists("grid"):
        os.makedirs("grid")

    grid_path = f"grid/{grid_basename}"
    grid.save(grid_path, "WEBP")

    context["image_path"] = os.path.abspath(grid_path)
    context["worker_host"] = os.environ["WORKER_HOST"]
    context["worker_ssh_port"] = os.environ["WORKER_SSH_PORT"]

    return context
