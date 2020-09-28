#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
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
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=True, default=True)
    seeking_description = db.Column(db.String(500))
    genres = db.Column(db.ARRAY(db.String(120)))

    artists = db.relationship("Show", back_populates="venue")

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=True, default=True)
    seeking_description = db.Column(db.String(500))

    venues = db.relationship("Show", back_populates="artist")

  
class Show(db.Model):
  __tablename__ = 'show'
  venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), primary_key=True)
  start_time = db.Column(db.DateTime, nullable=False)
  artist = db.relationship("Artist", back_populates="venues")
  venue = db.relationship("Venue", back_populates="artists")

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

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
  data = []
  cities = db.session.query(Venue).distinct(Venue.city).all()

  for city in cities:
    venues = db.session.query(Venue).filter(Venue.city == city.city).all()
    for venue in venues:
      num_shows = db.session.query(Show).filter(Show.venue_id == venue.id).count()

    item = {
      "city": city.city,
      "state": city.state,
      "venues": venues
            }

    data.append(item)
    
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term')
  venues = db.session.query(Venue).filter(Venue.name.contains(search_term)).all()

  data = []

  for venue in venues:
    data.append({
      "id": venue.id,
      "name": venue.name,
    })

  results={
    "count": len(data),
    "data": data
    }

  return render_template('pages/search_venues.html', results=results, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = db.session.query(Venue).get(venue_id)
  past_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id, Show.start_time < datetime.now()).all()
  upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id, Show.start_time > datetime.now()).all()

  past_shows_data = []
  upcoming_shows_data = []

  for show in past_shows_query:
    past_shows_data.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.start_time),
    })

  for show in upcoming_shows_query:
    upcoming_shows_data.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.start_time),
    })

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
    "past_shows": past_shows_data,
    "upcoming_shows": upcoming_shows_data,
    "upcoming_shows_count": len(upcoming_shows_data),
    "past_shows_count": len(upcoming_shows_data)
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
  error = False
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']

    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook_link)

    db.session.add(venue)
    db.session.commit()

    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('Error occured! Venue ' + request.form['name'] + ' could not be listed!')
    return render_template('pages/home.html')
  else:
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage

  try:
    db.session.query(Venue).filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = []
  artists = db.session.query(Artist).all()

  for artist in artists:
    new_artist = {
      "id": artist.id,
      "name": artist.name
    }
    data.append(new_artist)

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term')
  artists = db.session.query(Artist).filter(Artist.name.contains(search_term)).all()

  print("Suche " + str(request.form.get('search_term')))
  print("Gefunden " + str(artists))

  data = []

  for artist in artists:
    num_upcoming_shows = db.session.query(Show).join(Artist).filter(Show.artist_id == artist.id, Show.start_time > datetime.now()).count()

    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": num_upcoming_shows,
    })

  results={
    "count": len(data),
    "data": data
    }

  return render_template('pages/search_artists.html', results=results, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = db.session.query(Artist).get(artist_id)
  past_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id, Show.start_time < datetime.now()).all()
  upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id, Show.start_time > datetime.now()).all()

  past_shows_data = []
  upcoming_shows_data = []

  for show in past_shows_query:
    past_shows_data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": str(show.start_time),
    })

  for show in upcoming_shows_query:
    upcoming_shows_data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": str(show.start_time),
    })

  data = {
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
    "image_link": artist.image_link,
    "past_shows": past_shows_data,
    "upcoming_shows": upcoming_shows_data,
    "upcoming_shows_count": len(upcoming_shows_data),
    "past_shows_count": len(upcoming_shows_data)
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = db.session.query(Artist).get(artist_id)

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
    "image_link": artist.image_link,
  }

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  try:
    artist = db.session.query(Artist).get(artist_id)

    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form['facebook_link']

    db.session.commit()

    flash('Artist ' + request.form['name'] + ' was successfully edited!')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('Error occured! Artist ' + request.form['name'] + ' could not be edited!')
    return redirect(url_for('show_artist', artist_id=artist_id))
  else:
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = db.session.query(Venue).get(venue_id)

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
    "image_link": venue.image_link,
  }

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  try:
    venue = db.session.query(Venue).get(venue_id)

    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.address = request.form['address']
    venue.state = request.form['state']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form['facebook_link']

    db.session.commit()

    flash('Venue ' + request.form['name'] + ' was successfully edited!')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('Error occured! Venue ' + request.form['name'] + ' could not be edited!')
    return redirect(url_for('show_venue', venue_id=venue_id))
  else:
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']

    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link)

    db.session.add(artist)
    db.session.commit()

    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('Error occured! Artist ' + request.form['name'] + ' could not be listed!')
    return render_template('pages/home.html')
  else:
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = []

  shows = db.session.query(Show, Venue, Artist).join(Venue, Show.venue_id == Venue.id).join(Artist, Artist.id == Show.artist_id).all()

  for show in shows:
    new_show = {
			"venue_id": show.Venue.id,
			"venue_name": show.Venue.name,
			"artist_id": show.Artist.id,
			"artist_name": show.Artist.name,
			"artist_image_link": show.Artist.image_link,
			"start_time": str(show.Show.start_time)
    } 
    data.append(new_show)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']

    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)

    db.session.add(show)
    db.session.commit()

    flash('Show was successfully listed!')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('Error occured! Show could not be listed!')
    return render_template('pages/home.html')
  else:
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
