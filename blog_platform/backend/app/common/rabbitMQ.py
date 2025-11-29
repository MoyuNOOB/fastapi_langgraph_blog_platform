#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

import aio_pika
from backend.app.common.log import log
from backend.app.core.conf import settings
import json


class RabbitMQCli:
    def __init__(self):
        self._connection:aio_pika.RobustConnection | None= None
        self._channel:aio_pika.RobustChannel | None= None

    async def connect(self):
        if self._connection and not self._connection.is_closed:
            return

        try:
            self._connection = await aio_pika.connect_robust(
                host=settings.MQ_HOST,
                port=settings.MQ_PORT,
                login=settings.MQ_USER,
                password=settings.MQ_PASSWORD,
                virtualhost=settings.MQ_VHOST,
            )
            self._channel = await self._connection.channel()
        except Exception as e:
            log.error("连接 rabbitmq 异常 {}", e)
            sys.exit(1)

    async def get_channel(self) -> aio_pika.Channel:
        if not self._connection or self._connection.is_closed:
            await self.connect()
        if not self._channel or self._channel.is_closed:
            self._channel = await self._connection.channel()
        return self._channel

    #统一的发送消息函数
    async def publish(
        self,
        exchange_name:str,
        routing_key:str,
        message:str,
        exchange_type:aio_pika.ExchangeType = aio_pika.ExchangeType.DIRECT
    ):
        channel=await self.get_channel()
        exchange = await channel.declare_exchange(
            exchange_name,
            exchange_type,
            durable=True,
        )
        body=json.dumps(message).encode('utf-8')
        msg=aio_pika.Message(body=body)
        await exchange.publish(msg,routing_key=routing_key)
    
    async def init_rabbitmq_connect(self):
        await self.connect()

rabbitmq_client = RabbitMQCli()
