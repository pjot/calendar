#!/usr/bin/python

from gi.repository import Gtk, Gdk
from datetime import date, timedelta, datetime
import sqlite3
from threading import Timer
import math

class Week:
    def __init__(self, date):
        self.date = date
        self.set_properties()
        self.one_week = timedelta(7)

    def matches(self, date):
        same_year = self.year == date.year
        same_week = self.week == int(date.strftime('%W'))
        return same_year and same_week

    def set_properties(self):
        self.year = self.date.year
        self.week = int(self.date.strftime('%W')) + 1

    def increase(self):
        self.date = self.date + self.one_week
        self.set_properties()

    def decrease(self):
        self.date = self.date - self.one_week
        self.set_properties()

    def get_text(self):
        return str(self.year) + ' - W' + str(self.week)

class Month:
    def __init__(self, year, month):
        '''
        Creates a Month object which represent a month of a year

        :param year: Year
        :type year: int|str

        :param month: Month
        :type month: int|str
        '''
        self.year = int(year)
        self.month = int(month)
        my_date = date(self.year, self.month, 1)
        self.name = my_date.strftime('%B')

    def matches(self, day):
        '''
        Checks if a day matches this month

        :param day: Day
        :type day: CalendarDay|Month

        :returns: True if the day matches
        :rtype: bool
        '''
        if isinstance(day, CalendarDay):
            return self.year == day.date.year and self.month == day.date.month
        if isinstance(day, Month):
            return self.year == day.year and self.month == day.month


class EventEditor:
    def __init__(self, event, calendar_day):
        '''
        Creates an Event edit window

        :param date: Default date
        :type date: date
        '''
        self.event = event
        self.date = event.date
        self.calendar_day = calendar_day

        self.window = Gtk.Window()
        app_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Form grid
        grid = Gtk.Grid()
        grid.set_row_spacing(5)
        grid.set_column_spacing(5)

        # Name field
        grid.attach(Gtk.Label('Name', xalign=1), 0, 0, 1, 1)
        self.name_entry = Gtk.Entry()
        self.name_entry.set_text(self.event.name)
        grid.attach(self.name_entry, 1, 0, 1, 1)

        # Date field
        grid.attach(Gtk.Label('Date', xalign=1), 0, 1, 1, 1)
        self.date_entry = Gtk.Entry()
        self.date_entry.set_text(self.date.strftime('%Y-%m-%d'))
        grid.attach(self.date_entry, 1, 1, 1, 1)

        # Time field
        grid.attach(Gtk.Label('Time', xalign=1), 0, 2, 1, 1)

        time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        # Hours
        hour_store = Gtk.ListStore(int, str)
        for hour in range(0, 23):
            padded = str(hour)
            if hour < 10:
                padded = '0' + padded
            hour_store.append([hour, padded])
        self.hour_dropdown = Gtk.ComboBox.new_with_model(hour_store)
        renderer_text = Gtk.CellRendererText()
        self.hour_dropdown.pack_start(renderer_text, True)
        self.hour_dropdown.add_attribute(renderer_text, 'text', 1)
        self.hour_dropdown.set_property('has-frame', False)
        self.hour_dropdown.set_active(self.event.hour)
        time_box.add(self.hour_dropdown)

        time_box.pack_start(Gtk.Label(':'), False, False, 5)

        # Minutes
        minute_store = Gtk.ListStore(int, str)
        for minute in range(0, 59):
            padded = str(minute)
            if minute < 10:
                padded = '0' + padded
            minute_store.append([minute, padded])
        self.minute_dropdown = Gtk.ComboBox.new_with_model(minute_store)
        renderer_text = Gtk.CellRendererText()
        self.minute_dropdown.pack_start(renderer_text, True)
        self.minute_dropdown.add_attribute(renderer_text, 'text', 1)
        self.minute_dropdown.set_property('has-frame', False)
        self.minute_dropdown.set_active(self.event.minute)
        time_box.add(self.minute_dropdown)

        grid.attach(time_box, 1, 2, 1, 1)

        # Location field
        grid.attach(Gtk.Label('Location', xalign=1), 0, 3, 1, 1)
        self.location_entry = Gtk.Entry()
        self.location_entry.set_text(self.event.location)
        grid.attach(self.location_entry, 1, 3, 1, 1)

        # Button box
        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        # Filler
        buttons.pack_start(Gtk.Label(), True, True, 10)

        # Cancel button
        button = Gtk.Button('Cancel')
        button.connect('clicked', self.close)
        buttons.pack_start(button, False, True, 10)

        # Save button
        button = Gtk.Button('Save')
        button.connect('clicked', self.save)
        buttons.pack_start(button, False, True, 0)

        # Put everything together and show the window
        app_container.pack_start(grid, True, True, 10)
        app_container.pack_start(buttons, False, True, 10)
        app_container.set_margin_left(10)
        app_container.set_margin_right(10)
        self.window.add(app_container)

        self.window.show_all()

    def save(self, *args):
        '''
        Saves the event and closes the window
        '''
        event = self.event
        event.name = self.name_entry.get_text()
        event.location = self.location_entry.get_text()
        date = self.date_entry.get_text()
        event.date = datetime.strptime(date, '%Y-%m-%d').date()

        iterator = self.hour_dropdown.get_active_iter()
        model = self.hour_dropdown.get_model()
        # 0 is the id, 1 is the name
        event.hour = model[iterator][0]

        iterator = self.minute_dropdown.get_active_iter()
        model = self.minute_dropdown.get_model()
        # 0 is the id, 1 is the name
        event.minute = model[iterator][0]

        event.save()
        self.calendar_day.add_event(event)
        self.calendar_day.refresh_events()
        # Give the click event back to the Calendar Day
        self.calendar_day.is_blocked = False
        self.calendar_day.parent.update_gui()
        self.window.destroy()

    def close(self, *args):
        '''
        Closes the window
        '''
        self.calendar_day.is_blocked = False
        self.window.destroy()


class CalendarDisplay(Gtk.EventBox):
    def set_bg(self, color):
        '''
        Set the background of the box. Accepts ints between 0 and 256.

        :param color: Color tuple (red, green, blue)
        :type color: tuple
        '''
        red = color[0] / float(256)
        green = color[1] / float(256)
        blue = color[2] / float(256)
        color = Gdk.Color.from_floats(red, green, blue)
        self.modify_bg(Gtk.StateType.NORMAL, color)

    def add_event(self, event):
        for each in self.events:
            if each.id == event.id:
                return
        self.events.add(event)

    def _edit_event(self, area, *args):
        self.is_blocked = True
        EventEditor(Event.get_by_id(area.event_id), self)


class CalendarHour(CalendarDisplay):

    OTHER_DAY        = (220, 220, 220)
    BUSINESS_DAY     = (170, 170, 170)
    OTHER_WEEKEND    = (200, 200, 200)
    BUSINESS_WEEKEND = (150, 150, 150)
    OTHER_TODAY      = (150, 200, 150)
    BUSINESS_TODAY   = (120, 170, 120)

    def __init__(self, date, hour, parent):
        CalendarDisplay.__init__(self)
        self.date = date
        self.hour = hour
        self.parent = parent

        self.set_events()

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.label = Gtk.Label()
        self.grid = Gtk.Grid()
        self.label.set_alignment(0.1, 0.1)
        if self.date.weekday() == 0:
            self.main_box.add(self.label)
        self.main_box.add(self.grid)
        self.set_size_request(-1, 40)
        self.add(self.main_box)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.draw()
        self.refresh_events()

    def set_events(self):
        self.events = set()
        for event in Event.get_by_hour(self.date.year, self.date.month, self.date.day, self.hour):
            self.add_event(event)

    def refresh_events(self):
        '''
        Refresh the events in the view
        '''
        # Remove all widgets
        for widget in self.grid.get_children():
            widget.destroy()
        # Re-add them
        self.set_events()
        for i, event in enumerate(self.events):
            area = Gtk.DrawingArea()
            area.set_size_request(15, 15)
            color = Gdk.Color.from_floats(0.2, 0.5, 0.2)
            area.modify_bg(Gtk.StateType.NORMAL, color)
            area.event_id = event.id
            area.set_margin_top(5)
            area.set_margin_left(5)
            area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            area.connect('button-press-event', self._edit_event)
            # Add 5 events per row
            self.grid.attach(area, i % 5, i / 5, 1, 1)
        self.grid.show_all()

    def draw(self):
        if self.date.weekday() == 0:
            self.label.set_text(str(self.hour) + ':00')

        if self.hour > 8 and self.hour < 18:
            if self.date == date.today():
                self.set_bg(self.BUSINESS_TODAY)
                return
            if self.date.weekday() in [5, 6]:
                self.set_bg(self.BUSINESS_WEEKEND)
            else:
                self.set_bg(self.BUSINESS_DAY)
        else:
            if self.date == date.today():
                self.set_bg(self.OTHER_TODAY)
                return
            if self.date.weekday() in [5, 6]:
                self.set_bg(self.OTHER_WEEKEND)
            else:
                self.set_bg(self.OTHER_DAY)


class CalendarDay(CalendarDisplay):

    #                r    g    b
    EVEN_DAY     = (220, 220, 220)
    EVEN_WEEKEND = (200, 200, 200)
    ODD_DAY      = (170, 170, 170)
    ODD_WEEKEND  = (150, 150, 150)
    TODAY        = (150, 200, 150)

    ODD = (1, 3, 5, 7, 9, 11)

    def __init__(self, date, parent):
        '''
        Creates a CalendarDay object that represents a box in the main view.

        :param date: Date
        :type date: date
        '''
        CalendarDisplay.__init__(self)
        self.date = date
        self.parent = parent
        self.is_blocked = False

        self.events = set()
        for event in Event.get_by_day(date.year, date.month, date.day):
            self.add_event(event)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.grid = Gtk.Grid()
        self.grid.set_row_spacing(5)

        self.label = Gtk.Label()
        self.week_label = Gtk.Label()
        label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label_box.add(self.label)
        label_box.add(self.week_label)
        self.main_box.add(label_box)
        self.main_box.add(self.grid)
        # Days should be at least 80
        self.set_size_request(-1, 80)
        self.add(self.main_box)
        self.set_hexpand(True)
        self.set_vexpand(True)
        # Add some padding to the date string in the boxes
        self.label.set_alignment(0.05, 0.1)
        self.label.set_hexpand(True)
        self.week_label.set_alignment(0.95, 0.9)
        self.week_label.set_margin_right(5)
        self.label.modify_bg(Gtk.StateType.NORMAL, None)
        self.label.set_text('')
        self.refresh_events()

    def refresh_events(self):
        '''
        Refresh the events in the view
        '''
        # Remove all widgets
        for widget in self.grid.get_children():
            widget.destroy()
        # Re-add them
        for i, event in enumerate(self.events):
            area = Gtk.DrawingArea()
            area.set_size_request(15, 15)
            color = Gdk.Color.from_floats(0.2, 0.5, 0.2)
            area.modify_bg(Gtk.StateType.NORMAL, color)
            area.event_id = event.id
            area.set_margin_left(5)
            area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            area.connect('button-press-event', self._edit_event)
            # Add 5 events per row
            self.grid.attach(area, i % 5, i / 5, 1, 1)


    def __eq__(self, other):
        '''
        Enables comparisons with other CalendarDays

        :param other: Other object
        :type other: CalendarDay

        :returns bool: True if the date matches
        '''
        same_year = self.date.year == other.date.year
        same_month = self.date.month == other.date.month
        same_day = self.date.day == other.date.day
        return same_year and same_month and same_day

    def draw(self, current_month):
        '''
        Sets the color based upon the current month in the view

        :param current_month: Current month
        :type current_month: Month
        '''
        week_text = ''
        day_text = ''
        if self.date.year == self.parent.parent.year:
            day_text = self.date.strftime('%d')
            if self.date.weekday() == 6:
                week_text = str(int(self.date.strftime('%W')) + 1)
        else:
            self.label.set_text('')
            self.label.modify_bg(Gtk.StateType.NORMAL, None)
            return
        self.label.set_text(day_text)
        self.week_label.set_markup('<b>' + week_text + '</b>')
        if self.date == date.today():
            # Day is today
            self.set_bg(self.TODAY)
            return
        if self.date.month in self.ODD:
            if self.date.weekday() in [5, 6]:
                self.set_bg(self.ODD_WEEKEND)
            else:
                self.set_bg(self.ODD_DAY)
        else:
            if self.date.weekday() in [5, 6]:
                self.set_bg(self.EVEN_WEEKEND)
            else:
                self.set_bg(self.EVEN_DAY)


class Event:
    is_connected = False
    connection = None

    def __init__(self):
        '''
        Creates an Event object. This is a data model used to persist the
        events in a database as well as fetch them from it.
        '''
        self.is_saved = False
        self.name = ''
        self.time = ''
        self.id = ''
        self.location = ''

    def echo(self):
        '''
        Prints the details of this event. Useful for debugging.
        '''
        print 'Event:'
        print 'ID:', self.id
        print 'Name:', self.name
        print 'Location:', self.location
        print 'Hour:', self.hour
        print 'Minute:', self.minute
        print 'Year:', self.year
        print 'Month:', self.month
        print 'Day:', self.day

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
                hour, \
                minute \
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
        event.hour = int(row[5])
        event.minute = int(row[6])
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
        sql = 'select id from events where year = ? and month = ? and day = ? and hour = ?'
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
        Event.connection = sqlite3.connect('test.db')
        Event.is_connected = True
        sql = 'create table if not exists \
            events ( \
                id integer primary key, \
                name text, \
                location text, \
                year int, \
                month int, \
                day int, \
                hour int, \
                minute int \
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
        sql = 'insert into events \
                (name, location, year, month, day, hour, minute) \
                values \
                (?, ?, ?, ?, ?, ?, ?)'
        values = (
            self.name,
            self.location,
            self.date.strftime('%Y'),
            self.date.strftime('%m'),
            self.date.strftime('%d'),
            str(self.hour),
            str(self.minute)
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
                hour = ?, \
                minute = ?, \
                location = ? \
                where id = ?'
        values = (
            self.name,
            self.date.strftime('%Y'),
            self.date.strftime('%m'),
            self.date.strftime('%d'),
            str(self.hour),
            str(self.minute),
            self.location,
            self.id
        )
        cursor.execute(sql, values)
        connection.commit()

    def save(self):
        '''
        Persists the Event in the database.
        '''
        if self.is_saved:
            self._update()
        else:
            self._create()


class WeekView(Gtk.Box):
    days = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

    def __init__(self, parent):
        Gtk.Box.__init__(self)
        self.parent = parent
        self.is_new = True

        self.one_day = timedelta(1)

        self.scroller = Scroller()
        self.scroller.set_min_content_height(40)
        self.scroller.connect('size-allocate', self.initial_scroll)

        self.parent.previous_button.connect('clicked', self.decrease)
        self.parent.next_button.connect('clicked', self.increase)

        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(5)
        self.grid.set_row_spacing(5)
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)

        self.scroller.add(self.grid)
        self.add(self.scroller)

        self.current_week = Week(date.today())
        self.add_days()
        self.update_gui()

    def decrease(self, *args):
        self.current_week.decrease()
        self.add_days()
        self.update_gui()

    def increase(self, *args):
        self.current_week.increase()
        self.add_days()
        self.update_gui()

    def update_days(self):
        first_date = self.get_first_date()
        days = []
        for day in range(0, 7):
            days.append(self.days[day] + ' ' + first_date.strftime('%d'))
            first_date = first_date + self.one_day
        self.parent.set_day_labels(days)

    def get_first_date(self):
        first_date = self.current_week.date

        while first_date.weekday() != 0:
            first_date = first_date - self.one_day

        return first_date

    def add_days(self):
        first_date = self.get_first_date()

        for widget in self.grid.get_children():
            widget.destroy()

        # Add all hours in the week
        for day in range(0, 7):
            for hour in range(0, 23):
                calendar_hour = CalendarHour(first_date, hour, self)
                calendar_hour.date = first_date
                self.grid.attach(calendar_hour, day, hour, 1, 1)
            first_date = first_date + self.one_day

    def initial_scroll(self, *args):
        if self.is_new and self.scroller.is_initialized():
            self.scroller.scroll_to(8 * 45 - 5, fast=True)
            self.is_new = False

    def update_gui(self):
        self.grid.show_all()
        self.parent.week_label.set_text(self.current_week.get_text())
        for calendar_hour in self.grid.get_children():
            calendar_hour.refresh_events()


class Scroller(Gtk.ScrolledWindow):
    '''
    Check if the Scroller is initialized
    '''
    def is_initialized(self):
        return self.get_vadjustment().get_property('upper') != 1

    '''
    Scroll to a certain value of y. If fast == True, it animates the scrolling.
    '''
    def scroll_to(self, y=None, fast=False):
        adjustment = self.get_vadjustment()
        if fast:
            adjustment.set_value(y)
            return
        if y:
            self.target_y = y
            self.current_step = 4
        current_y = adjustment.get_value()
        current_delta = math.fabs(math.fabs(current_y) - self.target_y)
        if self.target_y != current_y:
            if current_delta < self.current_step:
                current_y = self.target_y
            else:
                if current_y > self.target_y:
                    current_y = current_y - self.current_step
                else:
                    current_y = current_y + self.current_step
            adjustment.set_value(current_y)
            if self.current_step < 200:
                self.current_step = self.current_step * 1.4
            Timer(0.02, self.scroll_to).start()


class FlexView(Gtk.Box):
    days = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

    def __init__(self, parent):
        '''
        Creates a Flex View.

        The Flex View is a view that displays an entire year with one box per
        day. It shades the months in different colors and allows the user to
        scroll through the weeks.

        :param parent: Parent window
        :type parent: CalendarWindow
        '''
        Gtk.Box.__init__(self)
        self.is_new = True
        self.parent = parent
        self.scroller = Scroller()
        self.scroller.set_min_content_height(40)
        self.scroller.connect('size-allocate', self.initial_scroll)

        # Calendar days
        self.grid = Gtk.Grid()
        self.grid.set_row_spacing(5)
        self.grid.set_column_spacing(5)
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.scroller.add(self.grid)

        self.add(self.scroller)

        self.scroller.connect('scroll-event', self.scrolling)
        self.parent.month_dropdown.connect('changed', self.month_changed)
        self.parent.year_dropdown.connect('changed', self.year_changed)
        self.parent.today_button.connect('clicked', self.goto_today)

        current_date = date.today()
        self.current_month = Month(current_date.year, current_date.month)
        self.set_year(current_date.year)

    def year_changed(self, combo):
        '''
        When the year is changed we should scroll to the new year

        :param combo: The year dropdown
        :type combo: Gtk.ComboBox
        '''
        if self.prevent_default:
            return
        iterator = combo.get_active_iter()
        model = combo.get_model()
        # 0 is the id, 1 is the name
        year = model[iterator][0]
        self.set_year(year)

    def set_year(self, year):
        year = int(year)
        # Prevent redrawing the same year
        if year == self.parent.year:
            return
        # Clear the CalendarDays
        for widget in self.grid.get_children():
            widget.destroy()
        # Add calendar days
        self.parent.year = year
        start_date = date(self.parent.year, 1, 1)
        day = timedelta(1)
        end_date = date(self.parent.year, 12, 31)
        x = 0
        y = 0
        while not start_date.weekday() == 0:
            start_date = start_date - day

        # Loop until we reach the end date
        while start_date < end_date:
            calendar_day = CalendarDay(start_date, self)
            if start_date.year == self.parent.year:
                calendar_day.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
                calendar_day.connect('button-press-event', self.date_click)
            self.grid.attach(calendar_day, x, y, 1, 1)
            # Iterate!
            start_date = start_date + day
            # Keep track of the coordinates in the grid
            if x == 6:
                x = 0
                y = y + 1
            else:
                x = x + 1

        self.current_month.year = self.parent.year
        self.draw()
        self.update_gui()

    def month_changed(self, combo):
        '''
        When the month is changed we should scroll to the new month

        :param combo: The month dropdown
        :type combo: Gtk.ComboBox
        '''
        if self.prevent_default:
            return
        iterator = combo.get_active_iter()
        model = combo.get_model()
        # 0 is the id, 1 is the name
        month = model[iterator][0]
        self.scroll_to(date(self.current_month.year, month, 1))

    def goto_today(self, *args):
        today = date.today()
        self.set_year(today.year)
        self.show_all()
        self.scroll_to(today)

    def initial_scroll(self, *args):
        if self.is_new and self.scroller.is_initialized():
            day_in_year = int(date.today().strftime('%j')) / 7
            scroll_top = day_in_year * 85 - 20
            self.scroller.scroll_to(scroll_top, fast=True)
            self.is_new = False

    def update_days(self):
        self.parent.set_day_labels(self.days)

    def scroll_to(self, to_date):
        '''
        Scrolls to a date by putting it at the top

        :param date: Date
        :type date: date
        '''
        day_in_year = int(to_date.strftime('%j')) + 1
        rows = day_in_year / 7
        day_top = rows * 85 - 20
        self.scroller.scroll_to(day_top)
        self.current_month.month = to_date.month
        self.current_month.year = to_date.year
        self.draw()
        self.update_gui()

    def get_calendar_day(self, date):
        '''
        Returns the CalendarDay of a date

        :param date: Date
        :type date: date

        :returns CalendarDay: The CalendarDay
        '''
        for day in self.grid.get_children():
            if day.date == date:
                return day

    def scrolling(self, *args):
        '''
        Calculates the current active month and updates the GUI accordingly
        '''
        days = {}
        parent_allocation = self.scroller.get_allocation()
        i = 0
        for day in self.grid.get_children():
            # One day per week is enough, speeds up calculation
            if not i == 7:
                i = i + 1
                continue
            i = 0
            # Get coordinates for this day relative to the scroll window
            allocation = day.get_allocation()
            coordinates = day.translate_coordinates(self.scroller, 0, 0)
            if coordinates:
                day_top = coordinates[1]
            else:
                day_top = 0

            above = 0 < day_top + allocation.height
            below = day_top < parent_allocation.height
            if above and below:
                # Day is visible
                year_month = day.date.strftime('%Y-%m')
                # Add to month count
                if not year_month in days.keys():
                    days[year_month] = 1
                else:
                    days[year_month] = days[year_month] + 1

        # Find the month with the most visible days
        year = ''
        month = ''
        current_max = 0
        for ym in days.keys():
            if current_max < days[ym]:
                current_max = days[ym]
                divided = ym.split('-')
                year = divided[0]
                month = divided[1]

        new_month = Month(year, month)
        # Only redraw if the current date has changed
        if not self.current_month.matches(new_month):
            self.current_month = new_month
            self.update_gui()

    def date_click(self, calendar_day, *args):
        '''
        Open an Event edit window for a CalendarDay

        :param calendar_day: The CalendarDay
        :type calendar_day: CalendarDay
        '''
        if not calendar_day.is_blocked:
            event = Event()
            event.date = calendar_day.date
            EventEditor(event, calendar_day)

    def draw(self):
        for day in self.grid.get_children():
            day.draw(self.current_month)

    def update_gui(self):
        '''
        Updates the GUI using the current active month
        '''
        self.prevent_default = True
        active_year = self.current_month.year - self.parent.START_YEAR
        self.parent.year_dropdown.set_active(active_year)
        self.parent.month_dropdown.set_active(self.current_month.month - 1)
        self.prevent_default = False

        self.parent.show_all()


class CalendarWindow(Gtk.Window):
    days = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

    START_YEAR = 2010
    END_YEAR = 2020

    def switcher_click(self, __, event):
        '''
        Somewhat hacky way of catching clicks in the stack switcher by
        comparing the click's x to the middle of the switcher. The first half
        of the switcher is the Week button and the second half is the Flex
        button.
        '''
        allocation = self.stack_switcher.get_allocation()
        if allocation.width / 2 < event.x:
            self.set_view('flex')
        else:
            self.set_view('week')

    def set_view(self, view):
        self.stack.set_visible_child_name(view)
        for widget in self.toolbar.get_children():
            self.toolbar.remove(widget)
        if view == 'week':
            self.current_view = self.week_view
            self.toolbar.add(self.week_box)
        else:
            self.current_view = self.flex_view
            self.toolbar.add(self.flex_box)
        self.current_view.initial_scroll()
        self.current_view.update_days()
        self.toolbar.show_all()

    def __init__(self):
        '''
        Creates a new Window and fills it with the interface
        '''
        Gtk.Window.__init__(self)

        self.set_icon_from_file('images/evolution-calendar.svg')
        self.set_title('Calendar')
        self.set_border_width(10)
        self.set_default_size(800, 600)
        self.year = 0
        self.show_week_dropdown = False
        self.app_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Toolbar
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        # View toolbar
        self.toolbar = Gtk.Box()
        self.flex_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.week_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        # Year dropdown
        year_store = Gtk.ListStore(int, str)
        for year in range(self.START_YEAR, self.END_YEAR):
            year_store.append([year, str(year)])
        self.year_dropdown = Gtk.ComboBox.new_with_model(year_store)
        renderer_text = Gtk.CellRendererText()
        self.year_dropdown.pack_start(renderer_text, True)
        self.year_dropdown.add_attribute(renderer_text, 'text', 1)
        self.year_dropdown.set_property('has-frame', False)
        self.flex_box.pack_start(self.year_dropdown, False, False, 0)

        # Month dropdown
        month_store = Gtk.ListStore(int, str)
        for i in range(1, 13):
            month_date = date(2010, i, 1)
            month_store.append([i, month_date.strftime('%B')])
        self.month_dropdown = Gtk.ComboBox.new_with_model(month_store)
        renderer_text = Gtk.CellRendererText()
        self.month_dropdown.pack_start(renderer_text, True)
        # Render the text, but use the number as id
        self.month_dropdown.add_attribute(renderer_text, "text", 1)
        self.month_dropdown.set_property('has-frame', False)
        self.flex_box.pack_start(self.month_dropdown, False, False, 10)

        # Today button
        self.today_button = Gtk.Button('Today')
        self.flex_box.pack_start(self.today_button, False, False, 0)

        # Week arrow left
        self.previous_button = Gtk.Button()
        left_arrow = Gtk.Arrow(Gtk.ArrowType.LEFT, Gtk.ShadowType.NONE)
        self.previous_button.add(left_arrow)
        self.week_box.pack_start(self.previous_button, False, False, 0)

        # Week arrow right
        self.next_button = Gtk.Button()
        right_arrow = Gtk.Arrow(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE)
        self.next_button.add(right_arrow)
        self.week_box.pack_start(self.next_button, False, False, 10)

        # Week label
        self.week_label = Gtk.Label()
        self.week_box.pack_start(self.week_label, False, False, 0)

        # View buttons
        self.stack = Gtk.Stack()
        self.stack.set_transition_duration(100)
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack_switcher = Gtk.StackSwitcher()
        self.stack_switcher.set_stack(self.stack)
        event_box = Gtk.EventBox()
        event_box.set_above_child(True)
        event_box.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        event_box.connect('button-press-event', self.switcher_click)
        event_box.add(self.stack_switcher)

        # Toolbar
        self.toolbar.add(self.week_box)
        box.pack_start(self.toolbar, True, True, 0)
        box.pack_start(event_box, False, False, 0)
        self.app_container.pack_start(box, False, True, 10)

        # Day names labels
        self.days_grid = Gtk.Grid()
        self.days_grid.set_column_spacing(5)
        self.days_grid.set_row_spacing(0)
        self.days_grid.set_column_homogeneous(True)
        self.days_grid.set_margin_right(15)
        self.app_container.pack_start(self.days_grid, False, True, 5)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.app_container.pack_start(separator, False, False, 10)

        # Add views
        self.week_view = WeekView(self)
        self.stack.add_titled(self.week_view, 'week', 'Week')

        self.flex_view = FlexView(self)
        self.stack.add_titled(self.flex_view, 'flex', 'Flex')

        self.current_view = self.week_view
        self.current_view.update_days()

        self.app_container.pack_start(self.stack, False, True, 5)

        self.add(self.app_container)
        self.show_all()

    def set_day_labels(self, labels):
        for widget in self.days_grid:
            widget.destroy()

        for x, day in enumerate(labels):
            label = Gtk.Label()
            label.set_text(day)
            label.set_vexpand(False)
            label.set_hexpand(False)
            self.days_grid.attach(label, x + 1, 0, 1, 1)
        self.days_grid.show_all()

win = CalendarWindow()
win.connect("delete-event", Gtk.main_quit)
Gtk.main()
