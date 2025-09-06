from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

# Association table for many-to-many relationship between users and liked posts
post_likes = Table(
    'post_likes',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('post_id', Integer, ForeignKey('posts.id'))
)

# Association table for many-to-many relationship between users and saved posts
post_saves = Table(
    'post_saves',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('post_id', Integer, ForeignKey('posts.id'))
)

# Association table for many-to-many relationship between users (followers)
user_followers = Table(
    'user_followers',
    Base.metadata,
    Column('follower_id', Integer, ForeignKey('users.id')),
    Column('following_id', Integer, ForeignKey('users.id'))
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    bio = Column(Text, default="")
    avatar_url = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = relationship("Post", back_populates="author")
    liked_posts = relationship("Post", secondary=post_likes, back_populates="liked_by")
    saved_posts = relationship("Post", secondary=post_saves, back_populates="saved_by")
    followers = relationship(
        "User", 
        secondary=user_followers,
        primaryjoin=id==user_followers.c.following_id,
        secondaryjoin=id==user_followers.c.follower_id,
        backref="following"
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat(),
            "followers_count": len(self.followers),
            "following_count": len(self.following)
        }

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    post_type = Column(String)  # blog, video, picture
    category = Column(String)   # entertainment, sports, school, etc.
    media_url = Column(String, default="")
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = relationship("User", back_populates="posts")
    liked_by = relationship("User", secondary=post_likes, back_populates="liked_posts")
    saved_by = relationship("User", secondary=post_saves, back_populates="saved_posts")
    comments = relationship("Comment", back_populates="post")
    
    def to_dict(self, user_id=None):
        post_dict = {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "post_type": self.post_type,
            "category": self.category,
            "media_url": self.media_url,
            "author": self.author.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "likes_count": len(self.liked_by),
            "comments_count": len(self.comments),
            "is_liked": False,
            "is_saved": False
        }
        
        if user_id:
            post_dict["is_liked"] = any(user.id == user_id for user in self.liked_by)
            post_dict["is_saved"] = any(user.id == user_id for user in self.saved_by)
            
        return post_dict

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    author = relationship("User")
    post = relationship("Post", back_populates="comments")
    
    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "author": self.author.to_dict(),
            "post_id": self.post_id,
            "created_at": self.created_at.isoformat()
        }

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
    
    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "sender": self.sender.to_dict(),
            "receiver": self.receiver.to_dict(),
            "created_at": self.created_at.isoformat(),
            "is_read": self.is_read
        }