from sqlalchemy.orm import Session
from models import User, Post


def get_post(session: Session, post_id: int):
    return session.query(Post).filter(Post.id == post_id).first()


def create_post(session: Session, author_id: int, title: str, content: str):
    new_post = Post(author_id=author_id, title=title, content=content)
    session.add(new_post)
    session.commit()
    return new_post


def update_post(session: Session, post_id: int, title: str, content: str):
    post = get_post(session, post_id)
    if post:
        post.title = title
        post.content = content
        session.commit()
    return post


def delete_post(session: Session, post_id: int):
    post = get_post(session, post_id)
    if post:
        session.delete(post)
        session.commit()
    return post


def get_user(session: Session, user_id: int):
    return session.query(User).filter(User.id == user_id).first()


def update_user(session: Session, user_id: int, username: str, email: str, bio: str):
    user = get_user(session, user_id)
    if user:
        user.username = username
        user.email = email
        user.bio = bio
        session.commit()
    return user
