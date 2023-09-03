from locust import HttpUser, task, between
import random
import json

class DoAPITest(HttpUser):

    @task
    def do_like(self):

        # user_id = random.randint(1, 90)

        #at backend, choose randomly between is_liked = True/False/None
        self.client.get(
            "api/test",
        )













