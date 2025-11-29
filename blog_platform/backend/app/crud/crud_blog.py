from tortoise.transactions import atomic

from backend.app.models.blog import Blog
from backend.app.schemas.blog import BlogCreate, BlogUpdate
from backend.app.crud.base import CRUDBase



class CRUDBlog(CRUDBase[Blog, BlogCreate, BlogUpdate]):

    #获取博客详情
    async def get_blog_by_id(self, pk: int) -> Blog:
        # if not await self.get(pk):
        #     raise errors.NotFoundError(msg='博客不存在')  DAO层不处理异常
        return await self.get(pk)
    #获取全站博客列表
    async def get_blog_list(self) -> list[Blog]:
        return await self.get_all()

    #获取用户博客列表
    async def get_blog_list_by_user(self, user_id: int) -> list[Blog]:
        return await self.model.filter(user_id=user_id).all()

    #创建博客
    @atomic()
    async def create_blog(self, data:dict) -> Blog:
        #data已经是dict了，里面有title,content,user_id,user_name
        return await self.model.create(**data)

    #更新博客
    @atomic()
    async def update_blog(self, pk: int, obj_in: BlogUpdate) -> Blog:
        return await self.update(pk, obj_in)

    #删除博客
    @atomic()
    async def delete_blog(self, pk: int) -> int:
        return await self.delete(pk)

BlogDao = CRUDBlog(Blog)
