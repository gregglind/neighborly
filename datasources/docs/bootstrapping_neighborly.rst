Bootstrapping Neighborly using Aggregation
============================================


Bootstrap
-----------

* Neighborly needs to be bootstrapped.  
* Until there are many users, no one will want to sign up
* content value grows the more content gets concentrated

To bootstrap, I propose using Google Calendar and Twitter feeds to
create events and threads


Why Start with Aggregation?
----------------------------

* hate logging in, especially the "yet another login" syndrome.
* aggregator easier to start with
* we don't need to own the user content (do we?)

Why GCal
---------
* Mature, well defined interface
* Users only need to post in one place
* semi-magical geocoding


Why Twitter
-----------
* tweets can be autopromoted to threads


Next Steps / Problems
------------------------
* find all Google Calendars for local non profits
* convince owners to start posting location info in the location field
* most people don't fill the location on their GCal items
* need a proper Neighborly api key for google maps api key
* geocoding using Google has terms of service limitations, 
  cf: http://www.google.com/apis/maps/terms.html


Code
------
* code lives in the neighborly/datasources/google_calendar 
