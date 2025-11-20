import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Post, Comment, Like

app = FastAPI(title="Social App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic helpers for responses
class UserOut(BaseModel):
    id: str
    name: str
    email: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class PostOut(BaseModel):
    id: str
    user_id: str
    content: str
    image_url: Optional[str] = None
    like_count: int
    comment_count: int


class CommentOut(BaseModel):
    id: str
    post_id: str
    user_id: str
    content: str


# Utility conversion

def doc_to_out(doc: dict) -> dict:
    if not doc:
        return {}
    d = {**doc}
    if d.get("_id"):
        d["id"] = str(d.pop("_id"))
    # convert ObjectId refs to str if present
    for k in ("user_id", "post_id"):
        if k in d:
            d[k] = str(d[k])
    return d


@app.get("/")
def read_root():
    return {"message": "Social App API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


# Seed minimal demo data endpoint
@app.post("/seed")
def seed_demo():
    # create or ensure a demo user
    user = User(name="Alex Johnson", email="alex@example.com", avatar_url=None, bio="Building a social app with AI ✨")
    user_id = create_document("user", user)

    # create a couple of posts
    p1 = Post(user_id=user_id, content="Hello world! This is my first post on our new app.", image_url=None)
    p2 = Post(user_id=user_id, content="Loving these floating icons in the hero animation.", image_url=None)
    create_document("post", p1)
    create_document("post", p2)

    return {"status": "ok", "user_id": user_id}


# Basic feeds
@app.get("/posts", response_model=List[PostOut])
def list_posts(limit: int = 20):
    docs = db["post"].find({}).sort("created_at", -1).limit(limit)
    return [PostOut(**doc_to_out(d)) for d in docs]


@app.post("/posts", response_model=PostOut)
def create_post(post: Post):
    new_id = create_document("post", post)
    doc = db["post"].find_one({"_id": ObjectId(new_id)})
    return PostOut(**doc_to_out(doc))


@app.get("/users", response_model=List[UserOut])
def list_users(limit: int = 20):
    docs = db["user"].find({}).sort("created_at", -1).limit(limit)
    return [UserOut(**doc_to_out(d)) for d in docs]


@app.post("/users", response_model=UserOut)
def create_user(user: User):
    new_id = create_document("user", user)
    doc = db["user"].find_one({"_id": ObjectId(new_id)})
    return UserOut(**doc_to_out(doc))


@app.post("/posts/{post_id}/like")
def like_post(post_id: str):
    try:
        _id = ObjectId(post_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post id")
    db["post"].update_one({"_id": _id}, {"$inc": {"like_count": 1}, "$set": {"updated_at": db.command('serverStatus')['localTime']}})
    doc = db["post"].find_one({"_id": _id})
    if not doc:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostOut(**doc_to_out(doc))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
