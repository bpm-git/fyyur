#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, String, Boolean, PickleType
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    genres = Column(PickleType, nullable=False)
    address = Column(String(120), nullable=False)
    city = Column(String(120), nullable=False)
    state = Column(String(120), nullable=False)
    phone = Column(String(120), nullable=False)
    website = Column(String(120))
    facebook_link = Column(String(120))
    seeking_talent = Column(Boolean, default=False)
    seeking_description = Column(String(500))
    image_link = Column(String(500))
    shows = db.relationship('Show', backref='Venue', lazy=True)

    def __repr__(self):
      return f'<Venue {self.id} {self.name}>'

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    genres = Column(PickleType, nullable=False)
    city = Column(String(120), nullable=False)
    state = Column(String(120), nullable=False)
    phone = Column(String(120), nullable=False)
    website = Column(String(120))
    facebook_link = Column(String(120))
    seeking_venue = Column(Boolean, default=False)
    seeking_description = Column(String(500))
    image_link = Column(String(500))
    shows = db.relationship('Show', backref='Artist', lazy=True)

    def __repr__(self):
      return f'<Artist {self.id} {self.name}>'

class Show(db.Model):
    __tablename__ = 'Show'

    id = Column(Integer, primary_key=True)
    venue_id = Column(Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = Column(Integer, db.ForeignKey('Artist.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)

    def __repr__(self):
      return f'<Show {self.id}, Venue {self.venue_id}, Artist {self.artist_id} >'
        
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
  
  data =[]

  all_venues = Venue.query.all()
  
  # Venue locations are grouped by city and state
  venues_in_citystate = set()
  for citystate in all_venues:
    venues_in_citystate.add((citystate.city, citystate.state))
  
  # add all the cities and state first
  for venue_locations in venues_in_citystate:
    data.append({
      "city": venue_locations[0],
      "state": venue_locations[1],
      "venues": []
    })
  
  # loop thru each venues per cities and state and add venue data in data along with number of shows per venue locations
  for venue in all_venues:
    num_upcoming_shows = 0   # initiare the counter
    shows_per_venue = Show.query.filter_by(venue_id=venue.id).all() # get all the shows for a venue
    
    # Increment number of shows when show start time is greater than current time
    for show in shows_per_venue:
      if show.start_time > datetime.now():
        num_upcoming_shows += 1
    
    # add each record in the data to return the output
    for venue_data in data:
      if venue.city == venue_data['city'] and venue.state == venue_data['state']:
        venue_data['venues'].append({
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": num_upcoming_shows
        })

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  
  search_term = request.form.get('search_term', '')
  all_venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

  response = {
    "count": len(all_venues),
    "data": []
  }

  for venue in all_venues:
    num_upcoming_shows = 0   # initiare the counter
    shows_per_venue = Show.query.filter_by(venue_id=venue.id).all() # get all the shows for a venue
    
    # Increment number of shows when show start time is greater than current time
    for show in shows_per_venue:
      if show.start_time > datetime.now():
        num_upcoming_shows += 1
    
    # add each record in the data to return the output
    response['data'].append({
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": num_upcoming_shows
      })

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # replace with real venue data from the venues table, using venue_id
  
  venue = Venue.query.filter_by(id=venue_id).one_or_none()
  all_shows = Show.query.filter_by(venue_id=venue_id).all()

  past_shows = []
  upcoming_shows = []
  
  # Get the past and upcoming shows
  for show in all_shows:
    if show.start_time > datetime.now():
      upcoming_shows.append({
        "artist_id": show.artist_id,
        "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
        "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
        "start_time": format_datetime(str(show.start_time))
      })
    else:
      past_shows.append({
        "artist_id": show.artist_id,
        "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
        "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
        "start_time": format_datetime(str(show.start_time))
      })

  # add each record in data and return
  data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
    }
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # insert form data as a new Venue record in the db, instead
  # modify data to be the data object returned from db insertion
  try:
    # Get the inputs from Venue Form
    form = VenueForm()
    new_name = form.name.data
    new_genres = form.genres.data
    new_address = form.address.data
    new_city = form.city.data
    new_state = form.state.data
    new_phone = form.phone.data
    new_website = form.website.data
    new_facebook_link = form.facebook_link.data

    if form.seeking_talent.data == 'Yes':
      new_seeking_talent = True
    else:
      new_seeking_talent = False

    new_seeking_description = form.seeking_description.data
    new_image_link = form.image_link.data

    new_venue = Venue(name=new_name,
                      genres=new_genres,
                      address=new_address,
                      city=new_city,
                      state=new_state,
                      phone=new_phone,
                      website=new_website,
                      facebook_link=new_facebook_link,
                      seeking_talent=new_seeking_talent,
                      seeking_description=new_seeking_description,
                      image_link=new_image_link)
    
    db.session.add(new_venue)
    db.session.commit()

    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  except:
    db.session.rollback()
    flash('Error! Venue ' + request.form['name'] + ' could not be listed')
    print(sys.exc_info())
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter_by(id=venue_id).first()
 
  # populate form with values from venue with ID <venue_id>
  venue={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
  }

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try:
    form = VenueForm()
    venue = Venue.query.filter_by(id=venue_id).first()
    
    venue.name = form.name.data
    venue.genres = form.genres.data
    venue.address = form.address.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.phone = form.phone.data
    venue.website = form.website.data
    venue.facebook_link = form.facebook_link.data

    if form.seeking_talent.data == 'Yes':
      venue.seeking_talent = True
    else:
      venue.seeking_talent = False

    venue.seeking_description = form.seeking_description.data
    venue.image_link = form.image_link.data

    db.session.commit()

    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully updated!')

  except:
    db.session.rollback()
    flash('Error! Venue ' + request.form['name'] + ' could not be updated')
    print(sys.exc_info())
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  try:
    # Get the venue to be deleted
    venue = Venue.query.filter(Venue.id == venue_id).first()
    venue_name = venue.name

    # all shows for that venue need to be deleted as well
    all_shows = Show.query.filter_by(venue_id=venue_id).all()

    # delete first the venue
    db.session.delete(venue)

    # Loop thru each shows to delete
    for show in all_shows:
      db.session.delete(show)

    db.session.commit()

    flash('Venue ' + venue_name + ' was successfully deleted!')
    flash('All shows for ' + venue_name + ' was successfully deleted!')
  except:
    db.session.rollback()
    flash('Error! Venue ' + venue_name + ' could not be deleted')
    print(sys.exc_info())
  finally:
    db.session.close()
  return jsonify({ 'success': True })


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  
  data = []

  all_artists = Artist.query.all()

  for artist in all_artists:
    data.append({
      "id": artist.id,
      "name": artist.name
    })

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  
  search_term = request.form.get('search_term', '')
  all_artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

  response = {
    "count": len(all_artists),
    "data": []
  }

  for artist in all_artists:
    num_upcoming_shows = 0   # initiare the counter
    shows_per_artist = Show.query.filter_by(artist_id=artist.id).all() # get all the shows for a venue
    
    # Increment number of shows when show start time is greater than current time
    for show in shows_per_artist:
      if show.start_time > datetime.now():
        num_upcoming_shows += 1
    
    # add each record in the data to return the output
    response['data'].append({
          "id": artist.id,
          "name": artist.name,
          "num_upcoming_shows": num_upcoming_shows
      })

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # replace with real venue data from the venues table, using venue_id

  artist = Artist.query.filter_by(id=artist_id).one_or_none()
  all_shows = Show.query.filter_by(artist_id=artist_id).all()

  past_shows = []
  upcoming_shows = []

  # Get all the upcoming and past shows
  for show in all_shows:
    if show.start_time > datetime.now():
      upcoming_shows.append({
        "venue_id": show.venue_id,
        "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
        "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link,
        "start_time": format_datetime(str(show.start_time))
      })
    else:
      past_shows.append({
        "venue_id": show.venue_id,
        "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
        "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link,
        "start_time": format_datetime(str(show.start_time))
      })

  # add the record in the data and return
  data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "seeking_venue": artist.seeking_venue,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
    }

  return render_template('pages/show_artist.html', artist=data)

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # insert form data as a new Venue record in the db, instead
  # modify data to be the data object returned from db insertion
  try:
    # Get the inputs from the Artist Form
    form = ArtistForm()
    new_name = form.name.data
    new_genres = form.genres.data
    new_city = form.city.data
    new_state = form.state.data
    new_phone = form.phone.data
    new_website = form.website.data
    new_facebook_link = form.facebook_link.data

    if form.seeking_venue.data == 'Yes':
      new_seeking_venue = True
    else:
      new_seeking_venue = False

    new_seeking_description = form.seeking_description.data
    new_image_link = form.image_link.data

    new_artist = Artist(name=new_name,
                        genres=new_genres,
                        city=new_city,
                        state=new_state,
                        phone=new_phone,
                        website=new_website,
                        facebook_link=new_facebook_link,
                        seeking_venue=new_seeking_venue,
                        seeking_description=new_seeking_description,
                        image_link=new_image_link)
    
    db.session.add(new_artist)
    db.session.commit()

    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  except:
    db.session.rollback()
    flash('Error! Artist ' + request.form['name'] + ' could not be listed')
    print(sys.exc_info())
  finally:
    db.session.close()

  return render_template('pages/home.html')

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.filter_by(id=artist_id).first()
  
  # populate form with fields from artist with ID <artist_id>
  artist={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    form = ArtistForm()
    artist = Artist.query.filter_by(id=artist_id).first()

    artist.name = form.name.data
    artist.genres = form.genres.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.website = form.website.data
    artist.facebook_link = form.facebook_link.data

    if form.seeking_venue.data == 'Yes':
      artist.seeking_venue = True
    else:
      artist.seeking_venue = False

    artist.seeking_description = form.seeking_description.data
    artist.image_link = form.image_link.data

    db.session.commit()

    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  except:
    db.session.rollback()
    flash('Error! Artist ' + request.form['name'] + ' could not be listed')
    print(sys.exc_info())
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  
  data = []
  all_shows = Show.query.all()

  for show in all_shows:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
      "artist_id": show.artist_id,
      "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
      "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
      "start_time": format_datetime(str(show.start_time))
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  try:
    form = ShowForm()
    new_artist_id = form.artist_id.data
    new_venue_id = form.venue_id.data
    new_start_time = form.start_time.data

    new_show = Show(artist_id=new_artist_id, 
                    venue_id=new_venue_id, 
                    start_time=new_start_time)
    
    db.session.add(new_show)
    db.session.commit()

    # on successful db insert, flash success
    flash('Show was successfully listed!')

  except:
    db.session.rollback()
    flash('Error! Show could not be listed')
    print(sys.exc_info())
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
