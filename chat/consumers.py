import json
from channels.generic.websocket import  AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Messages , Threads , CustomUser

class GroupMessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}_group'

        self.thread_check = await self.check_thread(self.room_name)

        if self.thread_check == False:
            await self.save_thread(name=self.room_name)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = text_data_json['user']


        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message_group',
                'message': message,
                'username': username
            }
        )

    # Receive message from room group
    async def chat_message_group(self, event):
        message = event['message']
        username = event['username']
        thread_name = await self.get_thread_name(self.room_name)
        sender = await self.get_user(username)
        if sender == self.scope['user']:
            await self.save_message(sender, thread_name ,message)
        

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'user':username,
            'group': self.room_group_name
            
        }))

    #saving message recieved
    @database_sync_to_async
    def save_message(self, user ,thread_name , content):
        Messages.objects.create(user_id=user,thread_name=thread_name,content=content)


    #retrieving user from database
    @database_sync_to_async
    def get_user(self, username):
        return CustomUser.objects.get(username=username)

    #retrieving current thread from database
    @database_sync_to_async
    def get_thread_name(self, thread_name):
        return Threads.objects.get(name=thread_name)



    #checking maybe thread already existed in database
    @database_sync_to_async
    def check_thread(self, name):
        return Threads.objects.filter(name=name).count() > 0


    #saving current thread to database
    @database_sync_to_async
    def save_thread(self, name):
        return Threads.objects.create(name=name , thread_type='group')





class DirectMessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.second_user_id = self.scope['url_route']['kwargs']['username']
        self.my_id = self.scope['user'].id
        if int(self.my_id) > int(self.second_user_id):
            self.room_group_name = f'chat_{self.my_id}{self.second_user_id}'

        else:
            self.room_group_name = f'chat_{self.second_user_id}{self.my_id}'

        self.thread_check = await self.check_thread(self.room_group_name)

        if self.thread_check == False:
            await self.save_thread(name=self.room_group_name)




        # Join room chat
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        #accepting connection
        await self.accept()

    #disconnecting the chat
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        message_sender = text_data_json['user']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': message_sender
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        user = event['user']
        group = self.room_group_name
        thread_name = await self.get_thread_name(group)
        sender = await self.get_user(user)
        if sender == self.scope['user']:
            await self.save_message(sender, thread_name ,message)

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'user': user,
            'group': group
        }))


    #saving message recieved
    @database_sync_to_async
    def save_message(self, user ,thread_name , content):
        Messages.objects.create(user_id=user,thread_name=thread_name,content=content)


    #retrieving user from database
    @database_sync_to_async
    def get_user(self, username):
        return CustomUser.objects.get(username=username)

    #retrieving current thread from database
    @database_sync_to_async
    def get_thread_name(self, thread_name):
        return Threads.objects.get(name=thread_name)



    #checking maybe thread already existed in database
    @database_sync_to_async
    def check_thread(self, name):
        return Threads.objects.filter(name=name).count() > 0


    #saving current thread to database
    @database_sync_to_async
    def save_thread(self, name):
        return Threads.objects.create(name=name , thread_type='direct')

