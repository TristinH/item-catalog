import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key=True)
	username = Column(String(100), nullable=False)
	email = Column(String(100))

class InstrumentCategory(Base):
	# Name of the table to store category info
	__tablename__ = 'category'

	# Fields for information to store
	id = Column(Integer, primary_key=True)
	category = Column(String(100), nullable=False)

	@property
	def serialize(self):
		# serialize object for JSON API
		return {
			'id': self.id,
			'category': self.category,
		}

class Instrument(Base):
	# Name of the table that stores individual
	# instrument info
	__tablename__ = 'instrument'

	# Columns for the info about the instrument
	id = Column(Integer, primary_key=True)
	name = Column(String(100), nullable=False)
	description = Column(String(300))
	brand = Column(String(50)) 
	color = Column(String(30))
	category = relationship(InstrumentCategory)
	category_id = Column(Integer, ForeignKey('category.id'))

	@property
	def serialize(self):
		# Serialize object for JSON API
		return {
			'id': self.id,
			'name': self.name,
			'description': self.description,
			'brand': self.brand,
			'color': self.color,
			'category_id': self.category_id,
		}

engine = create_engine('sqlite:///instrumentscatalog.db')
Base.metadata.create_all(engine)