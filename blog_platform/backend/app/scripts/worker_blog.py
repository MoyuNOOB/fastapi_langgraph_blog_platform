#写博客消费进程

import asyncio
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


async def main():
    await init_db()
    await redis_client.init_redis_connect()
    await rabbitmq_client.init_rabbitmq_connect()

    channel = await rabbitmq_client.get_channel()

    # 声明 exchange 和 queue
    exchange = await channel.declare_exchange(
        "blog.events",
        aio_pika.ExchangeType.DIRECT,
        durable=True,
    )
    queue = await channel.declare_queue(
        "blog.create.q",
        durable=True,
    )
    await queue.bind(exchange, routing_key="blog.create")

    log.info("Blog worker started, waiting for messages...")

    # 消费
    await queue.consume(handle_blog_create)

    # 阻塞等待
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())

    