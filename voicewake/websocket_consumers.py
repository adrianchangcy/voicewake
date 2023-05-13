# #channels version of Django views
# #respond and intiate requests, all while keeping an open connection

# import json
# from channels.generic.websocket import WebsocketConsumer
#     #for docs on channels, visit
#     #https://channels.readthedocs.io/en/latest/topics/consumers.html
# from asgiref.sync import async_to_sync


# class ChatConsumer(WebsocketConsumer):

#     def connect(self):

#         #here you supposedly pass the group info from user
#         self.room_group_name = 'test'

#         #on connect(), add this instance (?) to group
#         async_to_sync(self.channel_layer.group_add)(
#             self.room_group_name,
#             self.channel_name,
#         )

#         self.accept()

#     def receive(self, text_data):

#         text_data_json = json.loads(text_data)
#         message = text_data_json['message']

#         async_to_sync(self.channel_layer.group_send)(
#             self.room_group_name,
#             {
#                 'type': 'chat_message',
#                 'message': message,
#             }
#         )

#     def chat_message(self, event):
        
#         #every user who has a channel in the intended group will receive msg
#         #how does it determine the group???
#         message = event['message']

#         self.send(text_data=json.dumps({
#             'type': 'chat',
#             'message': message,
#         }))