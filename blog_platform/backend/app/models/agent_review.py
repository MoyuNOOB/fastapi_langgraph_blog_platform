from tortoise import Model, fields


class PostReviewSession(Model):

    id=fields.BigIntField(pk=True,index=True,description='主键id')
    post= fields.ForeignKeyField(
        "models.Blog",
        related_name="review_sessions",
        description="被审稿的博客"
    )
    user_id=fields.IntField(description='发起审稿的用户id')
    status=fields.IntField(description='状态：0=待处理,1=已完成,2=失败')

    created_time = fields.DatetimeField(
        auto_now_add=True,
        description="创建时间"
    )
    completed_time = fields.DatetimeField(
        null=True,
        description="完成时间"
    )
    meta = fields.JSONField(
        null=True,
        description="额外元信息（如tokens、耗时等）"
    )
    auto_apply = fields.BooleanField(
        default=False,
        description="是否自动应用修改"
    )

    class Meta:
        table = "post_review_session"
        table_description = "博客审稿会话"

class PostReviewResult(Model):
    id=fields.BigIntField(pk=True,index=True,description='主键id')
    session = fields.OneToOneField(
        "models.PostReviewSession",
        related_name="result",
        description="所属审稿会话"
    )
    issue_summary = fields.TextField(
        null=True,
        description="问题总体概览"
    )
    technical_issues = fields.TextField(
        null=True,
        description="技术错误/可疑点列表（Markdown或纯文本）"
    )
    style_issues = fields.TextField(
        null=True,
        description="风格/结构问题列表"
    )
    suggested_revision = fields.TextField(
        null=True,
        description="建议修改后的完整文章内容"
    )
    diff_view = fields.TextField(
        null=True,
        description="原文与修改后的差异说明或patch视图"
    )
    created_time = fields.DatetimeField(
        auto_now_add=True,
        description="结果生成时间"
    )

    class Meta:
        table = "post_review_result"
        table_description = "博客审稿结果"