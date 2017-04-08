""" Provide API for interacting with the database. """

import datetime as dt
import _mysql

from pymongo import *
from py2neo import Graph, Node, Relationship
from sqlalchemy import *

class UserDB():
	""" Superclass for all User database operations. """

	def __init__(self):
		engine = create_engine(
			"mysql+pymysql://root:passwd@localhost/userdb?host=localhost?port=3306")
		engine.echo = True
		self.conn = engine.connect()
		self.metadata = BoundMetaData(engine)

class UserCredDB(UserDB):
	""" User Credentials. """

	def __init__(self):
        super(UserCredDB, self).__init__()
        self.user_cred = Table('usercred', self.metadata, autoload=True)

	def insert(self, username, passwd):
		""" Create a new user. Called for Signup. """
		# Check if username already exists
		query = self.user_cred.select(self.user_cred.user_id == username)
		if(len(query)>0):
			return -1
		else:
			query = self.user_cred.insert()
			query.execute(user_id=username, password=passwd)
			return 1

	def authenticate(self, user, passwd):
		""" Authenticate a user. """
		query = self.user_cred.select(self.user_cred.user_id == username)
		if query.rowcount < 1:
			# No such user exists
			return -2
		elif query.rowcount == 1:
			if query['password'] != passwd:
				# Wrong password
				return -1
			else:
				# Successful
				return 1
class UserInfo(object):
	""" For session queries. """
	pass

class UserInfoDB(UserDB):
	""" Information about a user. """

	def __init__(self):
		super(UserInfoDB, self).__init__()
		self.userinfo = Table('usercred', self.metadata, autoload=True)
		userinfo_mapper = mapper(UserInfo, self.userinfo)
		self.session = create_session()

	def upsert(self, username, videoid, like=0, dislike=0):
		# Update or insert the video stats accordingly. 
		latest_timestamp = dt.datetime.today()
		data = session.query(UserInfo).first((self.userinfo.c.user_id==username) & (self.userinfo.c.videoid==videoid))
		if data is not None:
			data.latest_timestamp = latest_timestamp
			data.viewCount += 1
			data.like = like
			data.dislike = dislike
			session.save(data)
			session.flush()
		else:
			query = self.userinfo.insert()
			query.execute(user_id=username, videoid=videoid, latest_timestamp=latest_timestamp,
				viewCount=viewCount, like=like, dislike=dislike)
		return 1

	def get_info(self, username):
		query = self.userinfo.select(userinfo.c.user_id==username)
		query = query.execute()
		if query.rowcount == 0:
			return -1
		return query


class Video():
	""" Superclass for videos stored in MongoDB. """
	def __init__(self):
		self.client = MongoClient()
		self.db = self.client.yourtube
	
class Comments(Video):
	""" To store user comments for videos."""

	def __init__(self):
		super(Comments, self).__init__()
		self.collection = (self.db).comments

	def add_comment(self, username, videoid, comment):
		time = dt.datetime.today()
		self.collection.update(
			{ videoid: videoid },
			# { $addtoSet: {"comments": { by: username, timestamp: time, comment: comment }}}
			{ $push: { "comments": {
			$each: { "by": username, "timestamp": time, "comment": comment } } } }
			)
		return 1

	def get_comments(self, videoid):
		res = self.collection.find( { "videoid": videoid } )
		return res

class VideoInfo(Video):
	""" To store the entire videoinfo. Initial scraped info. """
	def __init__(self):
		super(VideoInfo, self).__init__()
		self.collection = (self.db).videoinfo

	def get(self, videoid):
		# Returns all docs for now.
		res = self.collection.find()
		return res

class HistoryTags(Video):
	""" To store tags accessed by this user in the past. """
	def __init__(self):
		super(HistoryTags, self).__init__()
		self.collection = (self.db).historytags

	def upsert_tag(self, username, tag):
		res = self.collection.update(
			{"user_id":username, "tags.tag":tag},
			{ $inc: {"tags.$.count"} })
		if res.modified_count == 0:
			db.students.update(
				{ "user_id": username },
				{$push: { tags: {
				$each: { "tag": tag, "count": 1 } } } }
				)
		return 1
	def get_tags(self, uername):
		res = self.collection.find("user_id":username)
		return res
