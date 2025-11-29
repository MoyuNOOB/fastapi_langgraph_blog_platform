from tortoise import Model, fields


class Blog(Model):
    id = fields.BigIntField(pk=True, index=True, description='主键id')
    title = fields.CharField(max_length=128, description='标题')
    content = fields.TextField(description='内容')
    user_id = fields.IntField(description='用户id')
    user_name = fields.CharField(max_length=128, description='用户名称')
    created_time = fields.DatetimeField(auto_now_add=True, description='创建时间')
    updated_time = fields.DatetimeField(auto_now=True, description='更新时间')

    class Meta:
        table = 'blog'