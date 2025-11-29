#博客接口数据模型

from typing import Optional
from datetime import datetime

from pydantic import BaseModel

class BlogCreate(BaseModel):
    title: str
    content: str

class BlogUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class BlogOut(BaseModel):
    id: int
    title: str
    content: str
    user_id: int
    user_name: str
    created_time: datetime
    updated_time: datetime

    #添加支持v1的orm_mode
    class Config:
        orm_mode = True


