from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReviewSessionBase(BaseModel):
    post_id: int
    user_id: int
    
class ReviewSessionCreate(ReviewSessionBase):
    auto_apply:bool=False


class ReviewSessionOut(ReviewSessionBase):
    id:int
    status: int  # 0=待处理,1=已完成,2=失败
    created_time:datetime
    completed_time: Optional[datetime]= None  #允许为none

    class Config:
        orm_mode = True

class ReviewResultOut(BaseModel):
    """
    审稿结果的返回
    """
    session_id: int
    issue_summary: Optional[str] = None
    technical_issues: Optional[str] = None
    style_issues: Optional[str] = None
    suggested_revision: Optional[str] = None
    diff_view: Optional[str] = None
    created_time: datetime

    class Config:
        orm_mode = True

class ReviewDetailOut(BaseModel):
    """
    合并会话 + 结果的详细返回
    """
    session: ReviewSessionOut
    result: Optional[ReviewResultOut] = None

class ApplyRevisionIn(BaseModel):
    """
    应用修改时的入参（可选允许用户再修一修）
    """
    override_content: Optional[str] = None