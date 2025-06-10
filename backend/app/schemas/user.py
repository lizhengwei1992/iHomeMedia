from pydantic import BaseModel


class Token(BaseModel):
    """
    访问令牌响应模型
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    令牌数据模型
    """
    username: str


class UserLogin(BaseModel):
    """
    用户登录请求模型
    """
    username: str
    password: str
