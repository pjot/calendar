#!/usr/bin/python

from gi.repository import Gtk, Gio, Gdk
from datetime import date, timedelta, datetime
import sqlite3

class Month ():
    def __init__ (self, year, month):
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

    def matches (self, day):
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

class EventEditor ():
    def __init__ (self, date, parent):
        '''
        Creates an Event edit window

        :param date: Default date
        :type date: date

        :param parent: Parent application
        :type parent: MyWindow
        '''
        self.date = date
        self.parent = parent

        self.window = Gtk.Window()
        app_container = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)

        # Form grid
        grid = Gtk.Grid()
        grid.set_row_spacing(5)
        grid.set_column_spacing(5)

        # Name field
        grid.attach(Gtk.Label('Name', xalign = 1), 0, 0, 1, 1)
        self.name_entry = Gtk.Entry()
        self.name_entry.set_text('Name')
        grid.attach(self.name_entry, 1, 0, 1, 1)

        # Date field
        grid.attach(Gtk.Label('Date', xalign = 1), 0, 1, 1, 1)
        self.date_entry = Gtk.Entry()
        self.date_entry.set_text(date.strftime('%Y-%m-%d'))
        grid.attach(self.date_entry, 1, 1, 1, 1)

        # Location field
        grid.attach(Gtk.Label('Location', xalign = 1), 0, 2, 1, 1)
        self.location_entry = Gtk.Entry()
        grid.attach(self.location_entry, 1, 2, 1, 1)

        # Button box
        buttons = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)

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

    def save (self, *args):
        '''
        Saves the event and closes the window
        '''
        event = Event()
        event.name = self.name_entry.get_text()
        event.location = self.location_entry.get_text()
        event.datetime = datetime.strptime(self.date_entry.get_text(), '%Y-%m-%d').date()
        event.save()
        calendar_day = self.parent.get_calendar_day(event.datetime)
        calendar_day.events.add(event)
        calendar_day.refresh_events()
        self.parent.set_month()
        self.window.destroy()

    def close (self, *args):
        '''
        Closes the window
        '''
        self.window.destroy()

class CalendarDay (Gtk.EventBox):

    def __init__ (self, date):
        Gtk.EventBox.__init__(self)
        self.date = date

        self.events = set()
        for event in Event.get_by_day(date.year, date.month, date.day):
            self.events.add(event)

        self.main_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        self.box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)
        self.label = Gtk.Label()
        self.main_box.add(self.label)
        self.main_box.add(self.box)
        # Days should be at least 80
        self.set_size_request(-1, 80)
#        self.add(self.label)
        self.add(self.main_box)
        self.set_hexpand(True)
        self.set_vexpand(True)
        # Add some padding to the date string in the boxes
        self.label.set_alignment(0.1, 0.1)
        self.label.modify_bg(Gtk.StateType.NORMAL, None)
        self.label.set_text('')
        self.refresh_events()

    def refresh_events (self):
        for widget in self.box.get_children():
            widget.destroy()
        for e in self.events:
            area = Gtk.DrawingArea()
            area.set_size_request(15, 15)
            area.modify_bg(Gtk.StateType.NORMAL, Gdk.Color.from_floats(0.2, 0.5, 0.2))
            self.box.pack_start(area, False, False, 5)

    def __eq__ (self, other):
        return self.date.year == other.date.year and self.date.month == other.date.month and self.date.day == other.date.day

    def draw (self, current_month):
        self.label.set_text(self.date.strftime('%d'))
        if self.date == date.today(): 
            self.set_bg(150, 200, 150)
            return
        if current_month.matches(self):
            if self.date.weekday() in [5, 6]:
                self.set_bg(150, 150, 150)
            else:
                self.set_bg(170, 170, 170)
        else:
            self.set_bg(220, 220, 220)

    def set_date (self, date):
        self.date = date
        if self.date.weekday() in [5, 6]:
            # Weekend
            self.set_bg(150, 150, 150)
        else:
            # Regular day
            self.set_bg(170, 170, 170)
        if self.date == date.today():
            # Today
            self.set_bg(150, 200, 150)
        self.label.set_text(date.strftime('%d'))

    def set_bg (self, r, g, b):
        self.modify_bg(Gtk.StateType.NORMAL, Gdk.Color.from_floats(r / float(256), g / float(256), b / float(256)))

class Event:
    is_connected = False
    connection = None

    def __init__ (self):
        self.is_saved = False

    def echo (self):
        print 'Event:'
        print 'ID:', self.id
        print 'Name:', self.name
        print 'Location:', self.location
        print 'Year:', self.year
        print 'Month:', self.month
        print 'Day:', self.day

    @staticmethod
    def get_by_id (id):
        connection = Event.get_connection()
        cursor = connection.cursor()
        cursor.execute('select name, location, year, month, day from events where id = ?', (str(id)))
        row = cursor.fetchone()
        event = Event()
        event.id = id
        event.name = row[0]
        event.location = row[1]
        event.year = row[2]
        event.month = row[3]
        event.day = row[4]
        event.is_saved = True
        return event

    @staticmethod
    def get_all ():
        connection = Event.get_connection()
        cursor = connection.cursor()
        cursor.execute('select id from events')
        rows = cursor.fetchall()
        objects = []
        for row in rows:
            objects.append(Event.get_by_id(row[0]))
        return objects

    @staticmethod
    def get_by_day (year, month, day):
        connection = Event.get_connection()
        cursor = connection.cursor()
        cursor.execute('select id from events where year = ? and month = ? and day = ?', (year, month, day))
        rows = cursor.fetchall()
        objects = []
        for row in rows:
            objects.append(Event.get_by_id(row[0]))
        return objects


    @staticmethod
    def connect ():
        Event.connection = sqlite3.connect('test.db')
        Event.is_connected = True
        Event.connection.cursor().execute('create table if not exists events (id integer primary key, name text, datetime datetime, location text, year int, month int, day int)')

    @staticmethod
    def get_connection ():
        if not Event.is_connected:
            Event.connect()
        return Event.connection

    def create (self):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute('insert into events (name, location, year, month, day) values (?, ?, ?, ?, ?)', (self.name, self.location, self.datetime.strftime('%Y'), self.datetime.strftime('%m'), self.datetime.strftime('%d')))
        connection.commit()
        self.id = cursor.lastrowid

    def update (self):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute('update events set name = ?, year = ?, month = ?, day = ?, location = ? where id = ?', (self.name, self.datetime.strftime('%Y'), self.datetime.strftime('%m'), self.datetime.strftime('%d'), self.location, self.id))
        connection.commit()

    def save (self):
        if self.is_saved:
            self.update()
        else:
            self.create()


class MyWindow (Gtk.Window):
    days = ['Week', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    START_YEAR = 2013
    END_YEAR = 2016

    def dummy (self, *args):
        pass

    def __init__ (self):
        Gtk.Window.__init__(self)

        self.set_border_width(10)
        self.set_default_size(800, 600)

        self.app_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                                                                        
        # Toolbar
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        # Year label
        year_store = Gtk.ListStore(int, str)
        for year in range(self.START_YEAR, self.END_YEAR):
            year_store.append([year, str(year)])
        self.year_dropdown = Gtk.ComboBox.new_with_model(year_store)
        renderer_text = Gtk.CellRendererText()
        self.year_dropdown.pack_start(renderer_text, True)
        self.year_dropdown.add_attribute(renderer_text, 'text', 1)
        self.year_dropdown.connect('changed', self.year_changed)
        self.year_dropdown.set_property('has-frame', False)
        box.pack_start(self.year_dropdown, False, False, 0)

        # Month dropdown
        month_store = Gtk.ListStore(int, str)
        for i in range(1, 12):
            month_date = date(2010, i, 1)
            month_store.append([i, month_date.strftime('%B')])
        self.month_dropdown = Gtk.ComboBox.new_with_model(month_store)
        renderer_text = Gtk.CellRendererText()
        self.month_dropdown.pack_start(renderer_text, True)
        # Render the text, but use the number as id
        self.month_dropdown.add_attribute(renderer_text, "text", 1)
        self.month_dropdown.connect("changed", self.month_changed)
        self.month_dropdown.set_property('has-frame', False)
        box.pack_start(self.month_dropdown, False, False, 10)

        # Filler
        box.pack_start(Gtk.Label(), True, True, 10)

        # View buttons
        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(1000)

        button = Gtk.Button('Day')
        button.connect('clicked', self.view_day)
        stack.add_titled(button, 'day', 'Day')

        button = Gtk.Button('Week')
        button.connect('clicked', self.view_day)
        stack.add_titled(button, 'week', 'Week')

        button = Gtk.Button('Flex')
        button.connect('clicked', self.view_day)
        stack.add_titled(button, 'flex', 'Flex')

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(stack)

        box.pack_start(stack_switcher, False, False, 0)

        self.app_container.pack_start(box, False, True, 10)

        self.scroller = Gtk.ScrolledWindow()
        self.scroller.set_min_content_height(40)
        self.scroller.connect('scroll-event', self.scrolling)

        # Calendar days
        self.grid = Gtk.Grid()
        self.grid.set_row_spacing(5)
        self.grid.set_column_spacing(5)
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.scroller.add(self.grid)

        # Day names labels
        days_grid = Gtk.Grid()
        days_grid.set_column_spacing(5)
        days_grid.set_row_spacing(0)
        days_grid.set_column_homogeneous(True)

        self.app_container.pack_start(days_grid, False, True, 10)
        self.app_container.pack_start(self.scroller, True, True, 10)

        self.add(self.app_container)

        # Add days labels
        for x in range(0, 8):
            label = Gtk.Label()
            label.set_text(self.days[x])
            label.set_vexpand(False)
            label.set_hexpand(False)
            days_grid.attach(label, x + 1, 0, 1, 1)

        # Add calendar days
        start_date = date(2014, 1, 1)
        day = timedelta(1)
        end_date = date(2015, 1, 1)
        x = 0
        y = 0
        while not start_date.weekday() == 0:
            start_date = start_date - day

        # Loop until we reach the end date
        while start_date < end_date:
            calendar_day = CalendarDay(start_date)
            if x == 6:
                # Add the week number
                week = int(start_date.strftime('%W')) + 1
                label = Gtk.Label(str(week))
                label.set_vexpand(False)
                label.set_hexpand(False)
                self.grid.attach(label, 0, y, 1, 1)
            calendar_day.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            calendar_day.connect('button-press-event', self.date_click)
            self.grid.attach(calendar_day, x + 1, y, 1, 1)
            # Iterate!
            start_date = start_date + day
            # Keep track of the coordinates in the grid
            if x == 6:
                x = 0
                y = y + 1
            else:
                x = x + 1

        # Initialize with today
        current_date = date.today()
        self.current_month = Month(current_date.year, current_date.month)
        self.set_month()
        # Trigger the redraw
        self.scrolling()

        events = Event.get_all()
        for event in events:
            event.echo()


    def view_day (self, *args):
        pass

    def year_changed (self, combo):
        pass

    def month_changed (self, combo):
        if self.prevent_default:
            return
        iterator = combo.get_active_iter()
        model = combo.get_model()
        # 0 is the id, 1 is the name
        month = model[iterator][0]
        self.scroll_to(date(self.current_month.year, month, 1))

    def scroll_to (self, date):
        parent_height = self.scroller.get_allocation().height
        # Search for the date
        for day in self.grid.get_children():
            if isinstance(day, Gtk.Label):
                continue
            if day.date == date:
                # Scroll the window
                day_top = day.get_allocation().y - parent_height / 20
                adjustment = self.scroller.get_vadjustment()
                adjustment.set_value(day_top)
                # Render the current month
                self.scrolling()
                return

    def get_calendar_day (self, date):
        for day in self.grid.get_children():
            if isinstance(day, Gtk.Label):
                continue
            if day.date == date:
                return day

    def scrolling (self, *args):
        days = {}
        parent_allocation = self.scroller.get_allocation()
        i = 0
        for day in self.grid.get_children():
            # Ignore week number labels
            if isinstance(day, Gtk.Label):
                continue
            # One day per month is enough, speeds up calculation
            if not i == 7:
                i = i + 1
                continue
            i = 0
            # Get coordinates for this day relative to the scroll window
            allocation = day.get_allocation()
            coordinates = day.translate_coordinates(self.scroller, 0, 0)
            day_top = coordinates[1]
            if 0 < day_top + allocation.height and day_top < parent_allocation.height:
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
            self.set_month()

    def date_click (self, calendar_day, event):
        win = EventEditor(calendar_day.date, self)

    def set_month (self):
        for day in self.grid.get_children():
            # Ignore week numbers
            if not isinstance(day, CalendarDay):
                continue
            day.draw(self.current_month)

        self.prevent_default = True
        self.year_dropdown.set_active(self.current_month.year - self.START_YEAR)
        self.month_dropdown.set_active(self.current_month.month - 1)
        self.prevent_default = False

        self.show_all()

win = MyWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()
