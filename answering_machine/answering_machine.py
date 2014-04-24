from willie.module import commands, nickname_commands, rule, priority
from willie.tools import Nick

from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from datetime import datetime
from os import path

basedir = path.abspath(path.dirname(__file__))
Base = declarative_base()
db = create_engine('sqlite:///' + path.join(basedir, 'data.sqlite'))
Session = sessionmaker(bind=db)

class Message(Base):
	__tablename__ = 'messages'
	id = Column(Integer, primary_key=True)
	nick_to = Column(String)
	nick_from = Column(String)
	msg = Column(Text)
	time_sent = Column(DateTime)

@commands('tell')
@nickname_commands('tell')
def catch_message(bot, trigger):
	sender = trigger.nick

	if not trigger.group(3):
		return bot.reply('Tell whom?')

	receiver = trigger.group(3).rstrip('.,:;')
	msg = trigger.group(2).lstrip(receiver).lstrip()
	receiver = receiver.lower()

	if not msg:
		return bot.reply('No message detected.')
	if len(receiver) > 20:
		return bot.reply('Nickname is too long.')
	if receiver == bot.nick:
		return bot.reply('Thanks for telling me that.')

	if not receiver in (Nick(sender), bot.nick, 'me'):
		time_sent = datetime.utcnow()

		message = Message(nick_to=receiver, nick_from=sender, msg=msg, time_sent=time_sent)
		session = Session()

		try:
			session.add(message)
			session.commit()
		except:
			session.rollback()
		finally:
			session.close()
		return bot.reply('Message stored.')
	elif Nick(sender) == receiver:
		return bot.say('You can tell yourself that!')

@rule('(.*)')
@priority('low')
def deliver_message(bot, trigger):
	receiver = trigger.nick
	session = Session()
	receiver = receiver.lower()

	if not session.query(Message).filter_by(nick_to=receiver).first():
		return

	messages = session.query(Message).filter_by(nick_to=receiver).all()
	for message in messages:
		bot.reply("%s says %s" % (message.nick_from, message.msg))
		try:
			session.delete(message)
			session.commit()
		except:
			session.rollback()
	session.close()
	return