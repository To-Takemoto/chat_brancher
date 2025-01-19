from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    IntegerField,
    ForeignKeyField,
    DateTimeField,
    TextField,
    )

import datetime

db = SqliteDatabase("data/app.db")

class User(Model):
    name = CharField(unique=True)
    password = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)
     
    class Meta:
        database = db

class TreeStructure(Model):
    owner = ForeignKeyField(User, backref='discussions')
    structure = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db

class Message(Model):
    chat = ForeignKeyField(TreeStructure, backref='messages')
    owner = ForeignKeyField(User, backref='messages')
    role = CharField()
    content = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)
    gen_id = CharField(null = True) 
    provider = CharField(null = True)
    object_ = CharField(null = True)
    created = CharField(null = True)
    finish_reason = CharField(null = True)
    index_ = CharField(null = True)
    message_role = CharField(null = True)
    message_refusal = CharField(null = True)
    prompt_tokens = IntegerField(null = True)
    completion_tokens = IntegerField(null = True)
    total_tokens = IntegerField(null = True)

    class Meta:
        database = db

# class UserMessage(Model):
#     discussion = ForeignKeyField(DiscussionStructure, backref='messages')
#     owner = ForeignKeyField(User, backref='user_messages')
#     content = CharField()
#     created_at = DateTimeField(default=datetime.datetime.now)

#     class Meta:
#         database = db

# class SystemMessage(Model):
#     discussion = ForeignKeyField(DiscussionStructure, backref='messages')
#     owner = ForeignKeyField(User, backref='user_messages')
#     content = CharField()
#     created_at = DateTimeField(default=datetime.datetime.now)

#     class Meta:
#         database = db