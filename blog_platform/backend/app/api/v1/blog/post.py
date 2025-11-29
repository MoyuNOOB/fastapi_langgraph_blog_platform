# blog接口
# 一般处理HTTP，请求验证，认证授权异常

from fastapi import APIRouter
from backend.app.service.blog_service import  get_all_blog_list,get_my_blog_list,get_blog_detail,create_blog_async_task,update_blog_async_task,delete_blog_async_task
from backend.app.schemas.blog import BlogCreate, BlogUpdate,BlogOut
from backend.app.api.jwt import get_current_user
from backend.app.models.user import User
from backend.app.common.response.response_schema import response_base
from backend.app.common.rabbitMQ import rabbitmq_client

from fastapi import Depends

blog = APIRouter()

@blog.post('/posts', summary='创建博客')
async def create_post(obj: BlogCreate, user: User = Depends(get_current_user)):
  await create_blog_async_task(obj,user)
  return response_base.response_200(
      msg='博客创建任务入队'
  )

@blog.get('/posts', summary='获取全站博客列表')
async def get_all_post_list():
    blog_list=await get_all_blog_list()
    blog_out_list=[BlogOut.from_orm(blog) for blog in blog_list]
    return response_base.response_200(
        msg='获取全站博客列表成功',
        data=blog_out_list
    )
@blog.get('/posts/my', summary='获取用户博客列表')
async def get_my_post_list(user: User = Depends(get_current_user)):
    blog_list=await get_my_blog_list(user.id)
    blog_out_list=[BlogOut.from_orm(blog) for blog in blog_list]
    return response_base.response_200(
        msg='获取用户博客列表成功',
        data=blog_out_list
    )

@blog.get('/posts/{post_id}', summary='获取博客详情')
async def get_post_detail(post_id: int):
    blog_out=await get_blog_detail(post_id)     #service层抛异常
    return response_base.response_200(
        msg='获取博客详情成功',
        data=blog_out
    )


@blog.put('/posts/{post_id}', summary='更新博客')
async def update_post(post_id: int, obj: BlogUpdate, user: User = Depends(get_current_user)):
    await update_blog_async_task(post_id, obj, user)
    return response_base.response_200(
        msg='博客更新任务入队'
    )

@blog.delete('/posts/{post_id}', summary='删除博客')
async def delete_post(post_id: int, user: User = Depends(get_current_user)):
    await delete_blog_async_task(post_id, user)
    return response_base.response_200(
        msg='博客删除任务入队'
    )

# @blog.put('/posts/{post_id}', summary='更新博客')
# async def update_post(post_id: int, obj: BlogUpdate, user: User = Depends(get_current_user)):
#     # post_id 作为 path 参数，只要进入路由肯定有值，可以不做非空判断
#     count=await update_blog(post_id, obj)   # 不存在会在 service 中抛 NotFoundError
#     return response_base.response_200(
#         msg='更新博客成功',
#         data={'updated':count}
#     )

# @blog.delete('/posts/{post_id}', summary='删除博客')
# async def delete_post(post_id: int, user: User = Depends(get_current_user)):
#     count=await delete_blog(post_id)
#     return response_base.response_200(
#         msg='删除博客成功',
#         data={'deleted':count}
#     )

@blog.get('/mq-test', summary='测试rabbitmq')
async def mq_test():
    await rabbitmq_client.publish(
        exchange_name='test',
        routing_key='test',
        message='test'
    )
    return response_base.response_200(
        msg='测试rabbitmq成功'
    )

