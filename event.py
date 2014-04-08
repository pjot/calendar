from datetime import date, timedelta, datetime

import sqlite3
import os


class Event:
    is_connected = False
    connection = None
    CONFIG_DIR = None

    def __init__(self):
        '''
        Creates an Event object. This is a data model used to persist the
        events in a database as well as fetch them from it.
        '''
        self.is_saved = False
        self.name = ''
        self.time = ''
        self.id = ''
        self.google_id = ''
        self.location = ''
        now = datetime.now()
        self.start_hour = now.hour
        self.start_minute = now.minute
        now = now + timedelta(hours=1)
        self.end_hour = now.hour
        self.end_minute = now.minute
        self.date = None

    def pad_zero(self, value):
        return_value = str(value)
        if int(value) < 10:
            return_value = '0' + return_value
        return return_value

    def to_google(self):
        if isinstance(self.date, date):
            self.year = self.date.strftime('%Y')
            self.month = self.date.strftime('%m')
            self.day = self.date.strftime('%d')
        start_string = '{}-{}-{}T{}:{}:00.000+01:00'.format(
            self.year,
            self.month,
            self.day,
            self.pad_zero(self.start_hour),
            self.pad_zero(self.start_minute)
        )
        end_string = '{}-{}-{}T{}:{}:00.000+01:00'.format(
            self.year,
            self.month,
            self.day,
            self.pad_zero(self.end_hour),
            self.pad_zero(self.end_minute)
        )
        return {
            'start': {
                'dateTime': start_string
            },
            'end': {
                'dateTime': end_string
            },
            'location': self.location,
            'summary': self.name
        }

    def echo(self):
        '''
        Prints the details of this event. Useful for debugging.
        '''
        print 'Event:'
        print 'ID:', self.id
        print 'Google ID:', self.google_id
        print 'Name:', self.name
        print 'Location:', self.location
        print 'Start Hour:', self.start_hour
        print 'Start Minute:', self.start_minute
        print 'End Hour:', self.end_hour
        print 'End Minute:', self.end_minute
        print 'Year:', self.year
        print 'Month:', self.month
        print 'Day:', self.day

    @staticmethod
    def get_by_google_id(id):
        cursor = Event.get_connection().cursor()
        sql = 'select id from events where google_id = ?'
        cursor.execute(sql, (id,))
        row = cursor.fetchone()
        if row is None:
            return Event()
        return Event.get_by_id(row[0])

    @staticmethod
    def get_by_id(id):
        '''
        Get one Event by its id

        :param id: ID
        :type id: int

        :returns Event: The Event
        '''
        cursor = Event.get_connection().cursor()
        sql = 'select \
                name, \
                location, \
                year, \
                month, \
                day, \
                start_hour, \
                start_minute, \
                end_hour, \
                end_minute, \
                google_id \
            from events where id = ?'
        cursor.execute(sql, (str(id),))
        row = cursor.fetchone()

        event = Event()
        event.id = id
        event.name = row[0]
        event.location = row[1]
        event.year = int(row[2])
        event.month = int(row[3])
        event.day = int(row[4])
        event.start_hour = int(row[5])
        event.start_minute = int(row[6])
        event.end_hour = int(row[7])
        event.end_minute = int(row[8])
        event.google_id = str(row[9])
        event.is_saved = True
        event.date = date(event.year, event.month, event.day)
        return event

    @staticmethod
    def get_all():
        '''
        Get all stored Events

        :returns list[Event]: List of Events
        '''
        cursor = Event.get_connection().cursor()
        cursor.execute('select id from events')
        rows = cursor.fetchall()
        objects = []
        for row in rows:
            objects.append(Event.get_by_id(row[0]))
        return objects

    @staticmethod
    def get_by_hour(year, month, day, hour):
        cursor = Event.get_connection().cursor()
        sql = 'select id \
                from events \
                where year = ? and month = ? and day = ? and start_hour = ?'
        cursor.execute(sql, (year, month, day, hour))
        rows = cursor.fetchall()
        objects = []
        for row in rows:
            objects.append(Event.get_by_id(row[0]))
        return objects

    @staticmethod
    def get_by_day(year, month, day):
        '''
        Get all events on a certain day.

        :param year: Year
        :type year: int

        :param month: Month
        :type month: int

        :param day: Day
        :type day: int

        :returns list[Event]: List of Events
        '''
        cursor = Event.get_connection().cursor()
        sql = 'select id from events where year = ? and month = ? and day = ?'
        cursor.execute(sql, (year, month, day))
        rows = cursor.fetchall()
        objects = []
        for row in rows:
            objects.append(Event.get_by_id(row[0]))
        return objects

    @staticmethod
    def connect():
        '''
        Connect to the database and create the schema if it does not exist.
        '''
        db_file = os.path.join(Event.CONFIG_DIR, 'events.db')
        Event.connection = sqlite3.connect(db_file)
        Event.connection.text_factory = str
        Event.is_connected = True
        sql = 'create table if not exists \
            events ( \
                id integer primary key, \
                name text, \
                location text, \
                year int, \
                month int, \
                day int, \
                start_hour int, \
                start_minute int, \
                end_hour int, \
                end_minute int, \
                google_id varchar(255) \
            )'
        Event.connection.cursor().execute(sql)

    @staticmethod
    def get_connection():
        '''
        Ensure that we are connected to the database and return the connection

        :returns sqlite3.Connection: Connection
        '''
        if not Event.is_connected:
            Event.connect()
        return Event.connection

    def _create(self):
        '''
        Create a new row in the database. Also sets the id of the event
        '''
        connection = self.get_connection()
        cursor = connection.cursor()
        if isinstance(self.date, date):
            self.year = self.date.strftime('%Y')
            self.month = self.date.strftime('%m')
            self.day = self.date.strftime('%d')
        sql = 'insert into events \
                ( \
                    name, \
                    location, \
                    year, \
                    month, \
                    day, \
                    start_hour, \
                    start_minute, \
                    end_hour, \
                    end_minute, \
                    google_id \
                ) \
                values \
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        values = (
            self.name,
            self.location.encode('utf-8'),
            self.year,
            self.month,
            self.day,
            str(self.start_hour),
            str(self.start_minute),
            str(self.end_hour),
            str(self.end_minute),
            self.google_id
        )
        cursor.execute(sql, values)
        connection.commit()
        self.id = cursor.lastrowid

    def _update(self):
        '''
        Update existing row in the database.
        '''
        connection = self.get_connection()
        cursor = connection.cursor()
        sql = 'update events set \
                name = ?, \
                year = ?, \
                month = ?, \
                day = ?, \
                start_hour = ?, \
                start_minute = ?, \
                end_hour = ?, \
                end_minute = ?, \
                location = ?, \
                google_id = ? \
                where id = ?'
        values = (
            self.name,
            self.date.strftime('%Y'),
            self.date.strftime('%m'),
            self.date.strftime('%d'),
            str(self.start_hour),
            str(self.start_minute),
            str(self.end_hour),
            str(self.end_minute),
            self.location.encode('utf-8'),
            self.google_id,
            self.id
        )
        cursor.execute(sql, values)
        connection.commit()

    def save(self):
        '''
        Persists the Event in the database.
        '''
        if self.location is None:
            self.location = ''
        if self.is_saved:
            self._update()
        else:
            self._create()
