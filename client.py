import requests
import sys
import os
import time


class DramaClient:
    BASE_URL = "https://rdrama.net"

    def __init__(self):
        self.token = os.environ.get("RDRAMA_TOKEN", "")
        self.last_processed_id = 2821161  # Most recent comment seen.

    def get(self, endpoint):
        print(endpoint)
        time.sleep(5)

        r = requests.get(
            f"{self.BASE_URL}{endpoint}", headers={"Authorization": self.token}
        )

        if r.status_code != 200:
            print("Error!", r, r.status_code, r.content)
            sys.exit(1)

        return r.json()["data"]

    def post(self, endpoint, payload, files=[]):
        print(endpoint)
        time.sleep(5)

        r = requests.post(
            f"{self.BASE_URL}{endpoint}",
            payload,
            headers={"Authorization": self.token},
            files=files,
        )

        if r.status_code != 200:
            print("Error!", r, r.status_code, r.content)
            sys.exit(1)

        return r.json()

    def fetch_new_comments(self):
        comments = []
        if self.last_processed_id is None:
            comments += self.fetch_page(1)
        else:
            earliest_id = None
            page = 1
            # Fetch comments until we find the last one processed.
            while earliest_id is None or earliest_id > self.last_processed_id:
                page_comments = self.fetch_page(page)
                earliest_id = min([c["id"] for c in page_comments])
                comments += [
                    c for c in page_comments if c["id"] > self.last_processed_id
                ]
                page += 1

        if not comments:
            return []

        self.last_processed_id = max(c["id"] for c in comments)

        # New comments may have pushed others to page n+1 while fetching.
        deduped_comments = {c["id"]: c for c in comments}.values()

        # Oldest first.
        comments.reverse()

        return comments

    def fetch_page(self, page):
        return self.get(f"/comments?page={page}")

    def reply(self, parent_fullname, submission, body, image_path=None):
        payload = {
            "parent_fullname": parent_fullname,
            "submission": submission,
            "body": body,
        }

        files = []
        if image_path:
            filename = image_path.split("/")[-1]
            files = {"file": (filename, open(image_path, "rb"), "image/webp")}

        self.post("/comment", payload, files=files)
