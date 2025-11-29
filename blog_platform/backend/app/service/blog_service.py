#blog服务
import json
from backend.app.common.log import log
from backend.app.crud.crud_blog import BlogDao
from backend.app.schemas.blog import BlogCreate, BlogUpdate
from backend.app.common.exception.errors import ForbiddenError, NotFoundError
from backend.app.models.user import User
from backend.app.common.redis import redis_client
from backend.app.common.rabbitMQ import rabbitmq_client
from backend.app.schemas.blog import BlogOut
from backend.app.core.conf import settings

'''
创建博客，更新博客，删除博客，获取博客列表，获取博客详情
'''

# async def create_blog(obj:BlogCreate,cur_user:User):
#     '''
#     写性能优化：优先保证DB一致性，把缓存当副本
#     '''
#     if not obj.title or not obj.content:
#         raise ForbiddenError(msg='标题和内容不能为空')
#     #将schema转成字典，再补上用户信息
#     data=obj.dict()
#     data.update({
#         'user_id':cur_user.id,
#         'user_name':cur_user.username
#     })
#     blog=await BlogDao.create_blog(data)
#     #创建成功后删除缓存
#     await redis_client.delete(f"blog:list:user:{blog.user_id}")
#     return blog

#并发创建博客
async def create_blog_async_task(data:BlogCreate,cur_user:User):
    message={
        "event":"blog.create",
        "data":{
            "title":data.title,
            "content":data.content,
            "user_id":cur_user.id,
            "user_name":cur_user.username
        }
    }
    log.info(" send blog.create mq message: {}", message)

    await rabbitmq_client.publish(
        exchange_name='blog.events',
        routing_key='blog.create',
        message=message
    )

#并发更新博客
async def update_blog_async_task(pk:int,obj:BlogUpdate,cur_user:User):
    message={
        "event":"blog.update",
        "data":{
            "id":pk,
            "title":obj.title,
            "content":obj.content,
            "user_id":cur_user.id,
            "user_name":cur_user.username
        }
    }
    log.info(" send blog.update mq message: {}", message)

    await rabbitmq_client.publish(
        exchange_name='blog.events',
        routing_key='blog.update',
        message=message
    )

#并发删除博客
async def delete_blog_async_task(pk:int,cur_user:User):
    message={
        "event":"blog.delete",
        "data":{
            "id":pk,
            "user_id":cur_user.id,
            "user_name":cur_user.username
        }
    }
    log.info(" send blog.delete mq message: {}", message)

    await rabbitmq_client.publish(
        exchange_name='blog.events',
        routing_key='blog.delete',
        message=message
    )


# async def update_blog(pk:int,obj:BlogUpdate):
#     '''
#     业务校验，调用dao层更新博客
#     '''
#     blog=await BlogDao.get_blog_by_id(pk)
#     if not blog:
#         raise NotFoundError(msg='博客不存在')
#     count=await BlogDao.update_blog(pk,obj)
#     #更新成功后删除缓存
#     await redis_client.delete(f"blog:detail:{pk}")
#     await redis_client.delete(f"blog:list:user:{blog.user_id}")
#     return count

# async def delete_blog(pk:int):
#     '''
#     业务校验，调用dao层删除博客
#     '''
#     blog=await BlogDao.get_blog_by_id(pk)
#     if not blog:
#         raise NotFoundError(msg='博客不存在')
#     count=await BlogDao.delete_blog(pk)
#     #删除成功后删除缓存
#     await redis_client.delete(f"blog:detail:{pk}")
#     await redis_client.delete(f"blog:list:user:{blog.user_id}")
#     return count

async def get_all_blog_list():
    '''
    业务校验，调用dao层获取全站博客列表
    '''
    return await BlogDao.get_blog_list()

async def get_my_blog_list(user_id:int):
    '''
    读优化：先查缓存，未命中再查数据库，最后回写缓存
    '''
    redis_key=f"blog:list:user:{user_id}"
    #读缓存
    cache_data=await redis_client.get(redis_key)
    if cache_data:
        data_dict=json.loads(cache_data)
        blog_out_list=[BlogOut(**data_dict) for data_dict in data_dict]
        return blog_out_list
    #缓存未命中
    blog_list=await BlogDao.get_blog_list_by_user(user_id)
    blog_out_list=[BlogOut.from_orm(blog) for blog in blog_list]
    #回写缓存
    await redis_client.set(
        redis_key,
        json.dumps([b.dict() for b in blog_out_list],default=str),
        ex=settings.REDIS_EXPIRE_TIME
    )
    return blog_out_list

async def get_blog_detail(pk:int):
    '''
    读优化：先查缓存，未命中再查数据库，最后回写缓存
    '''
    cache_key=f"blog:detail:{pk}"
    #读缓存
    cache_data=await redis_client.get(cache_key)
    #缓存命中
    if cache_data:
        #redis里面存的是json数据，还原成BlogOut
        data_dict=json.loads(cache_data)
        blog_out=BlogOut(**data_dict)
        return blog_out
    #缓存未命中
    blog=await BlogDao.get_blog_by_id(pk)
    if not blog:
        raise NotFoundError(msg='博客不存在')
    blog_out=BlogOut.from_orm(blog)
    #回写缓存
    await redis_client.set(
        cache_key,
        json.dumps(blog_out.dict(),default=str),
        ex=settings.REDIS_EXPIRE_TIME
    )
    return blog_out