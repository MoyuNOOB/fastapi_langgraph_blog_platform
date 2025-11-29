#写博客消费进程,由registar.py注册

import aio_pika
import json
from backend.app.common.rabbitMQ import rabbitmq_client
from backend.app.common.redis import redis_client
from backend.app.crud.crud_blog import BlogDao
from backend.app.common.log import log
from tortoise import Tortoise
from backend.app.database.db_mysql import db_config



async def init_db():
    await Tortoise.init(config=db_config)

#处理博客创建队列消息
async def handle_blog_create(message:aio_pika.IncomingMessage):
    async with message.process():
        log.info("recieve blog.create mq message: {}", message)
        payload=json.loads(message.body.decode('utf-8'))
        data = payload['data']

        #写数据库，调Dao层方法
        await BlogDao.create_blog({
            'title':data['title'],
            'content':data['content'],
            'user_id':data['user_id'],
            'user_name':data['user_name']
        })
        #删除缓存
        await redis_client.delete(f"blog:list:user:{data['user_id']}")

#处理博客删除队列消息
async def handle_blog_delete(message:aio_pika.IncomingMessage):
    async with message.process():
        log.info("recieve blog.delete mq message: {}", message)
        payload=json.loads(message.body.decode('utf-8'))
        data = payload['data']

        #写数据库，调Dao层方法
        await BlogDao.delete_blog(data['id'])
        #删除缓存
        await redis_client.delete(f"blog:detail:{data['id']}")
        await redis_client.delete(f"blog:list:user:{data['user_id']}")

#处理博客更新队列消息
async def handle_blog_update(message:aio_pika.IncomingMessage):
    async with message.process():
        log.info("recieve blog.update mq message: {}", message)
        payload=json.loads(message.body.decode('utf-8'))
        data = payload['data']
        obj_in = BlogUpdate(title=data['title'], content=data['content'])        #写数据库，调Dao层方法
        await BlogDao.update_blog(data['id'],obj_in)
        #删除缓存
        await redis_client.delete(f"blog:detail:{data['id']}")
        await redis_client.delete(f"blog:list:user:{data['user_id']}")

async def start_blog_consumers():
    await init_db() 

    # 声明 channel，exchange
    channel = await rabbitmq_client.get_channel()

    exchange = await channel.declare_exchange(
        "blog.events",
        aio_pika.ExchangeType.DIRECT,
        durable=True,
    )
   
    #create
    queue_create=await channel.declare_queue(
        "blog.create.q",
        durable=True,
    )
    await queue_create.bind(exchange, routing_key="blog.create")
    await queue_create.consume(handle_blog_create)

    #delete
    queue_delete=await channel.declare_queue(
        "blog.delete.q",
        durable=True,
    )
    await queue_delete.bind(exchange, routing_key="blog.delete")
    await queue_delete.consume(handle_blog_delete)

    #update
    queue_update=await channel.declare_queue(
        "blog.update.q",
        durable=True,
    )
    await queue_update.bind(exchange, routing_key="blog.update")
    await queue_update.consume(handle_blog_update)

    log.info("Blog consumers started, waiting for messages...")


    