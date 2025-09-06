from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_
from typing import List, Optional
from datetime import datetime, timedelta
import os
import shutil
import uuid

from database import get_db, init_db
from auth import get_current_user, create_access_token, get_password_hash, authenticate_user
from models import User, Post, Comment, Message, post_likes, post_saves, user_followers

app = FastAPI(title="Chyrp API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
os.makedirs("uploads/images", exist_ok=True)
os.makedirs("uploads/videos", exist_ok=True)

# Mount static files for serving uploaded media
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("startup")
async def on_startup():
    await init_db()

# Authentication endpoints
@app.post("/token")
async def login_for_access_token(
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }

@app.post("/register")
async def register_user(
    email: str = Form(...),
    username: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # Check if user already exists
    result = await db.execute(select(User).filter(
        or_(User.email == email, User.username == username)
    ))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(password)
    new_user = User(
        email=email,
        username=username,
        full_name=full_name,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Generate access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": new_user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": new_user.to_dict()
    }

# User endpoints
@app.get("/users/me", response_model=dict)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user.to_dict()

@app.put("/users/me")
async def update_user_profile(
    full_name: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if full_name:
        current_user.full_name = full_name
    if bio:
        current_user.bio = bio
    
    if avatar:
        # Save avatar file
        file_extension = avatar.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"uploads/images/{filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(avatar.file, buffer)
        
        current_user.avatar_url = f"/uploads/images/{filename}"
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user.to_dict()

@app.get("/users/{username}", response_model=dict)
async def get_user_profile(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).filter(User.username == username))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user.to_dict()

# Follow/unfollow endpoints
@app.post("/users/{username}/follow")
async def follow_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot follow yourself"
        )
    
    result = await db.execute(select(User).filter(User.username == username))
    user_to_follow = result.scalars().first()
    
    if not user_to_follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user_to_follow not in current_user.following:
        current_user.following.append(user_to_follow)
        await db.commit()
    
    return {"message": f"Now following {username}"}

@app.delete("/users/{username}/follow")
async def unfollow_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).filter(User.username == username))
    user_to_unfollow = result.scalars().first()
    
    if not user_to_unfollow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user_to_unfollow in current_user.following:
        current_user.following.remove(user_to_unfollow)
        await db.commit()
    
    return {"message": f"Unfollowed {username}"}

# Post endpoints
@app.get("/posts", response_model=List[dict])
async def get_posts(
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    filter_type: Optional[str] = None,  # all, saved, liked
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Post).order_by(Post.created_at.desc())
    
    # Apply category filter
    if category and category != "all":
        query = query.filter(Post.category == category)
    
    # Apply saved/liked filter
    if filter_type == "saved":
        query = query.filter(Post.saved_by.any(id=current_user.id))
    elif filter_type == "liked":
        query = query.filter(Post.liked_by.any(id=current_user.id))
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    posts = result.scalars().all()
    
    return [post.to_dict(current_user.id) for post in posts]

@app.post("/posts", response_model=dict)
async def create_post(
    title: str = Form(...),
    content: str = Form(...),
    post_type: str = Form(...),
    category: str = Form(...),
    media: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    media_url = None
    
    if media:
        # Save media file
        file_extension = media.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{file_extension}"
        
        if post_type == "video":
            file_path = f"uploads/videos/{filename}"
            media_url = f"/uploads/videos/{filename}"
        else:  # picture or other
            file_path = f"uploads/images/{filename}"
            media_url = f"/uploads/images/{filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(media.file, buffer)
    
    new_post = Post(
        title=title,
        content=content,
        post_type=post_type,
        category=category,
        media_url=media_url,
        author_id=current_user.id
    )
    
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    
    return new_post.to_dict(current_user.id)

@app.get("/posts/{post_id}", response_model=dict)
async def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalars().first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    return post.to_dict(current_user.id)

@app.put("/posts/{post_id}", response_model=dict)
async def update_post(
    post_id: int,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    media: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalars().first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this post"
        )
    
    if title:
        post.title = title
    if content:
        post.content = content
    if category:
        post.category = category
    
    if media:
        # Save media file
        file_extension = media.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{file_extension}"
        
        if post.post_type == "video":
            file_path = f"uploads/videos/{filename}"
            post.media_url = f"/uploads/videos/{filename}"
        else:  # picture or other
            file_path = f"uploads/images/{filename}"
            post.media_url = f"/uploads/images/{filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(media.file, buffer)
    
    post.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(post)
    
    return post.to_dict(current_user.id)

@app.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalars().first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this post"
        )
    
    await db.delete(post)
    await db.commit()
    
    return {"message": "Post deleted successfully"}

@app.get("/users/{username}/posts", response_model=List[dict])
async def get_user_posts(
    username: str,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).filter(User.username == username))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    query = select(Post).filter(Post.author_id == user.id).order_by(Post.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    posts = result.scalars().all()
    
    return [post.to_dict(current_user.id) for post in posts]

# Like endpoints
@app.post("/posts/{post_id}/like")
async def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalars().first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    if current_user not in post.liked_by:
        post.liked_by.append(current_user)
        await db.commit()
    
    return {"message": "Post liked", "likes_count": len(post.liked_by)}

@app.delete("/posts/{post_id}/like")
async def unlike_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalars().first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    if current_user in post.liked_by:
        post.liked_by.remove(current_user)
        await db.commit()
    
    return {"message": "Post unliked", "likes_count": len(post.liked_by)}

# Save endpoints
@app.post("/posts/{post_id}/save")
async def save_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalars().first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    if current_user not in post.saved_by:
        post.saved_by.append(current_user)
        await db.commit()
    
    return {"message": "Post saved"}

@app.delete("/posts/{post_id}/save")
async def unsave_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalars().first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    if current_user in post.saved_by:
        post.saved_by.remove(current_user)
        await db.commit()
    
    return {"message": "Post unsaved"}

# Comment endpoints
@app.get("/posts/{post_id}/comments", response_model=List[dict])
async def get_post_comments(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalars().first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    return [comment.to_dict() for comment in post.comments]

@app.post("/posts/{post_id}/comments", response_model=dict)
async def create_comment(
    post_id: int,
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Post).filter(Post.id == post_id))
    post = result.scalars().first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    new_comment = Comment(
        content=content,
        author_id=current_user.id,
        post_id=post_id
    )
    
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    
    return new_comment.to_dict()

# Message endpoints
@app.get("/messages", response_model=List[dict])
async def get_messages(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get all messages where current user is either sender or receiver
    query = select(Message).filter(
        or_(
            Message.sender_id == current_user.id,
            Message.receiver_id == current_user.id
        )
    ).order_by(Message.created_at.desc())
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return [message.to_dict() for message in messages]

@app.get("/messages/{user_id}", response_model=List[dict])
async def get_conversation(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Message).filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == user_id),
            and_(Message.sender_id == user_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.asc())
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    # Mark messages as read
    for message in messages:
        if message.receiver_id == current_user.id and not message.is_read:
            message.is_read = True
    
    await db.commit()
    
    return [message.to_dict() for message in messages]

@app.post("/messages/{user_id}", response_model=dict)
async def send_message(
    user_id: int,
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if receiver exists
    result = await db.execute(select(User).filter(User.id == user_id))
    receiver = result.scalars().first()
    
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    new_message = Message(
        content=content,
        sender_id=current_user.id,
        receiver_id=user_id
    )
    
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    
    return new_message.to_dict()

# Search endpoint
@app.get("/search")
async def search(
    q: str,
    search_type: str = "posts",  # posts, users
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if search_type == "users":
        query = select(User).filter(
            or_(
                User.username.ilike(f"%{q}%"),
                User.full_name.ilike(f"%{q}%")
            )
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        return [user.to_dict() for user in users]
    
    else:  # search posts
        query = select(Post).filter(
            or_(
                Post.title.ilike(f"%{q}%"),
                Post.content.ilike(f"%{q}%")
            )
        ).order_by(Post.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        posts = result.scalars().all()
        
        return [post.to_dict(current_user.id) for post in posts]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)