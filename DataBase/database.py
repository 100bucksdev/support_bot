import random
from datetime import datetime, UTC
import os

from sqlalchemy import inspect, Boolean, DateTime, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

from sqlalchemy import Column, String, Integer

DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()


class Operators(Base):
    __tablename__ = "operators"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=True)
    custom_id = Column(Integer, unique=True, nullable=False)
    is_busy = Column(Boolean, default=False)
    busy_with_chat = Column(String, nullable=True)


class Chat(Base):
    __tablename__ = "chatbot_chat"

    id = Column(Integer, primary_key=True)
    chat_code = Column(String(255), unique=True, nullable=False)
    is_operator_called = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(UTC))


class Message(Base):
    __tablename__ = "chatbot_message"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chatbot_chat.id"), nullable=False)
    text = Column(String(2500), nullable=False)
    sender = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))

    chat = relationship("Chat", back_populates="messages")


Chat.messages = relationship("Message", order_by=Message.id, back_populates="chat")


class Database:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)

        inspector = inspect(self.engine)
        if not inspector.has_table(Operators.__tablename__):
            Base.metadata.create_all(self.engine)

    def add_operator(self, telegram_id):
        session = self.Session()
        try:
            custom_id = self.generate_custom_operator_id()
            new_operator = Operators(telegram_id=telegram_id, custom_id=custom_id)
            session.add(new_operator)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def generate_custom_operator_id(self):
        session = self.Session()
        while True:
            custom_id = random.randint(100, 999)
            exists = session.query(Operators).filter_by(custom_id=custom_id).first()
            if not exists:
                return custom_id

    def update_operator(self, telegram_id, **kwargs):
        session = self.Session()
        try:
            operator = (
                session.query(Operators).filter_by(telegram_id=telegram_id).first()
            )
            if not operator:
                raise ValueError("Operator not found")

            for key, value in kwargs.items():
                if hasattr(operator, key):
                    setattr(operator, key, value)

            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_operator(self, telegram_id):
        session = self.Session()
        operator = session.query(Operators).filter_by(telegram_id=telegram_id).first()
        session.close()
        return operator

    def get_operator_by_chat_code(self, chat_code):
        session = self.Session()
        operator = session.query(Operators).filter(Operators.busy_with_chat == chat_code).first()
        session.close()
        return operator

    def get_chat_history(self, chat_id: str):
        session = self.Session()
        chat = session.query(Chat).filter(Chat.chat_code == chat_id).first()

        if not chat:
            return ["❌ No messages found for this chat."]

        messages = (
            session.query(Message)
            .filter(Message.chat_id == chat.id)
            .order_by(Message.created_at)
            .all()
        )

        chat_history = ""
        chat_parts = []

        for message in messages:
            sender = message.sender
            text = message.text

            new_entry = f"{f"🤖 {sender.upper()}" if sender.upper() == 'AI' else f'👤 {sender.upper()}'}: {text}\n\n"

            if len(chat_history) + len(new_entry) > 4096:
                chat_parts.append(chat_history)
                chat_history = new_entry
            else:
                chat_history += new_entry

        if chat_history:
            chat_parts.append(chat_history)

        return chat_parts if chat_parts else ["❌ No messages found for this chat."]
