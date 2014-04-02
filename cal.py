#!/usr/bin/python

from gi.repository import Gtk, Gdk
from datetime import date, timedelta, datetime
import sqlite3


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

        :param parent: Parent application
        :type parent: MyWindow
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

        # Location field
        grid.attach(Gtk.Label('Location', xalign=1), 0, 2, 1, 1)
        self.location_entry = Gtk.Entry()
        self.location_entry.set_text(self.event.location)
        grid.attach(self.location_entry, 1, 2, 1, 1)

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


class CalendarDay(Gtk.EventBox):

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
        Gtk.EventBox.__init__(self)
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
        self.main_box.add(self.label)
        self.main_box.add(self.grid)
        # Days should be at least 80
        self.set_size_request(-1, 80)
        self.add(self.main_box)
        self.set_hexpand(True)
        self.set_vexpand(True)
        # Add some padding to the date string in the boxes
        self.label.set_alignment(0.05, 0.1)
        self.label.modify_bg(Gtk.StateType.NORMAL, None)
        self.label.set_text('')
        self.refresh_events()

    def add_event(self, event):
        for each in self.events:
            if each.id == event.id:
                return
        self.events.add(event)

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

    def _edit_event(self, area, *args):
        self.is_blocked = True
        EventEditor(Event.get_by_id(area.event_id), self)

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
        self.label.set_text(self.date.strftime('%d'))
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
                day \
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
                day int \
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
                (name, location, year, month, day) \
                values \
                (?, ?, ?, ?, ?)'
        values = (
            self.name,
            self.location,
            self.date.strftime('%Y'),
            self.date.strftime('%m'),
            self.date.strftime('%d')
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
                location = ? \
                where id = ?'
        values = (
            self.name,
            self.date.strftime('%Y'),
            self.date.strftime('%m'),
            self.date.strftime('%d'),
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


class MyWindow(Gtk.Window):
    days = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

    START_YEAR = 2014
    END_YEAR = 2018

    def __init__(self):
        '''
        Creates a new Window and fills it with the interface
        '''
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
        self.year_dropdown.connect('changed', self._year_changed)
        self.year_dropdown.set_property('has-frame', False)
        box.pack_start(self.year_dropdown, False, False, 0)

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
        self.month_dropdown.connect("changed", self._month_changed)
        self.month_dropdown.set_property('has-frame', False)
        box.pack_start(self.month_dropdown, False, False, 10)

        # Today button
        button = Gtk.Button('Today')
        button.connect('clicked', self._goto_today)
        box.pack_start(button, False, False, 0)

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
        self.scroller.connect('scroll-event', self._scrolling)

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
        days_grid.set_margin_right(15)

        self.app_container.pack_start(days_grid, False, True, 5)
        self.app_container.pack_start(self.scroller, True, True, 10)

        self.add(self.app_container)

        # Add days labels
        for x, day in enumerate(self.days):
            label = Gtk.Label()
            label.set_text(day)
            label.set_vexpand(False)
            label.set_hexpand(False)
            days_grid.attach(label, x + 1, 0, 1, 1)

        # Add calendar days
        start_date = date(self.START_YEAR, 1, 1)
        day = timedelta(1)
        end_date = date(self.END_YEAR, 1, 1)
        x = 0
        y = 0
        while not start_date.weekday() == 0:
            start_date = start_date - day

        # Loop until we reach the end date
        while start_date < end_date:
            calendar_day = CalendarDay(start_date, self)
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

        # Initialize with today
        current_date = date.today()
        self.current_month = Month(current_date.year, current_date.month)
        self.draw()
        self.update_gui()
        self._goto_today()

    def view_day(self, *args):
        pass

    def _year_changed(self, combo):
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
        self.scroll_to(date(year, self.current_month.month, 1))

    def _month_changed(self, combo):
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

    def _goto_today(self, *args):
        self.scroll_to(date.today())

    def scroll_to(self, date):
        '''
        Scrolls to a date by putting it at the top

        :param date: Date
        :type date: date
        '''
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
                self._scrolling()
                return

    def get_calendar_day(self, date):
        '''
        Returns the CalendarDay of a date

        :param date: Date
        :type date: date

        :returns CalendarDay: The CalendarDay
        '''
        for day in self.grid.get_children():
            if isinstance(day, Gtk.Label):
                continue
            if day.date == date:
                return day

    def _scrolling(self, *args):
        '''
        Calculates the current active month and updates the GUI accordingly
        '''
        days = {}
        parent_allocation = self.scroller.get_allocation()
        i = 0
        for day in self.grid.get_children():
            # One day per month is enough, speeds up calculation
            if not i == 7:
                i = i + 1
                continue
            i = 0
            # Get coordinates for this day relative to the scroll window
            allocation = day.get_allocation()
            coordinates = day.translate_coordinates(self.scroller, 0, 0)
            day_top = coordinates[1]

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
        active_year = self.current_month.year - self.START_YEAR
        self.year_dropdown.set_active(active_year)
        self.month_dropdown.set_active(self.current_month.month - 1)
        self.prevent_default = False

        self.show_all()

win = MyWindow()
win.connect("delete-event", Gtk.main_quit)
Gtk.main()
