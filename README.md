Desktop Calendar written in Python
----------------------------------

To run it just do ./calendar in the repo. I'm not sure which packages it depends on yet.

This is a desktop calendar application inspired by gnome-calendar and the Android stock calendar app. I've been using Thunderbird with Lightning as my desktop calendar for ages, but I've always wanted something prettier so started writing this. As of right now, most of it is broken but the main features are already visible.

The application has three main views: Day view, Week view and Flex view.

##Day view
The Day view is a view of the events of a day, placed neatly even if they overlap:
![alt_text](https://github.com/pjot/calendar/raw/master/images/day_view.png)

* Clicking an event allows you to edit it
* Overlapping events will be places side by side

##Week view
The Week view is your regular view of a week, with the days in columns. It looks like this:
![alt text](https://github.com/pjot/calendar/raw/master/images/week_view.png)

* Clicking the boxes will eventually bring up the Create Event view
* The view is scrollable and the default view is centered around the business hours (which also have a different color than the other hours)

##Flex view
The Flex view is my version of the view in the Android calendar app which consists of one box per day in a long scrollable container. It colors the months in different colors, as well as highlighting the weekends. 
![alt text](https://github.com/pjot/calendar/raw/master/images/flex_view.png)

* Clicking a box brings up the Create Event view
* Clicking an event (the small green squares) brings up en Edit Event view
* At startup the view is centered around today (which is highlighted in green)

## Toolbar
Certain elements in the toolbar are common for the views and some change:
* Today - Moves the focus of the view to today
* Plus - Imports a .ical file
* Sync/Refresh - Imports all events from the selected Google Calendar
* Settings - Opens the settings dialog
