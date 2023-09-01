from locust import HttpUser, task, between

class DoAPITest(HttpUser):

    wait_time = between(1, 2)

    @task
    def do_like(self):
        self.client.post('api/event-likes-dislikes', json={'event_id': 102, 'is_liked': True})

    @task
    def do_dislike(self):
        self.client.post('api/event-likes-dislikes', json={'event_id': 102, 'is_liked': False})

    @task
    def remove_like_dislike(self):
        self.client.post('api/event-likes-dislikes', json={'event_id': 102, 'is_liked': None})











