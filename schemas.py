"""
Database Schemas for the Social App

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase of the class name.

- User -> user
- Post -> post
- Comment -> comment
- Like -> like
"""
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl, EmailStr


class User(BaseModel):
    name: str = Field(..., description="Display name")
    email: EmailStr = Field(..., description="Unique email address")
    avatar_url: Optional[HttpUrl] = Field(None, description="Profile avatar URL")
    bio: Optional[str] = Field(None, max_length=280, description="Short bio")


class Post(BaseModel):
    user_id: str = Field(..., description="Author user id (string ObjectId)")
    content: str = Field(..., min_length=1, max_length=1000, description="Post text content")
    image_url: Optional[HttpUrl] = Field(None, description="Optional image URL")
    like_count: int = Field(0, ge=0)
    comment_count: int = Field(0, ge=0)


class Comment(BaseModel):
    post_id: str = Field(..., description="Related post id (string ObjectId)")
    user_id: str = Field(..., description="Author user id (string ObjectId)")
    content: str = Field(..., min_length=1, max_length=500)


class Like(BaseModel):
    post_id: str = Field(..., description="Related post id (string ObjectId)")
    user_id: str = Field(..., description="User who liked (string ObjectId)")
