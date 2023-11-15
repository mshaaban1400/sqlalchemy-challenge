# Import the dependencies.
from flask import Flask, jsonify
import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt



#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///../hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

# Convert the query results from your precipitation analysis (i.e. retrieve only the last 12 months of data) to a dictionary using `date` as the key and `prcp` as the value.
# Return the JSON representation of your dictionary.
@app.route('/api/v1.0/precipitation')
def precipitation():
    # Calculate the date 1 year ago from the last data point in the database
    most_recent_date = session.query(measurement.date).order_by(measurement.date.desc()).first()
    one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)

    # Query precipitation data for the last 12 months
    results = session.query(measurement.date, measurement.prcp, measurement.tobs).filter(
    measurement.date >= one_year_ago,
    measurement.date <= dt.date(2017, 8, 23),
    ).all()

    # Convert the query results to a dictionary
    precipitation_data = {date: prcp for date, prcp in results}

    return jsonify(precipitation_data)

# Return a JSON list of stations from the dataset.
@app.route('/api/v1.0/stations')
def stations():
    # Query all stations
    results = session.query(station.station).all()

    # Convert the query results to a list
    station_list = [result for result, in results]

    return jsonify(station_list)

# Query the dates and temperature observations of the most-active station for the previous year of data. Return a JSON list of temperature observations for the previous year.
@app.route('/api/v1.0/tobs')
def tobs():
    # Query the most active station
    active_stations_query = session.query(
    measurement.station,
    func.count().label('row_count')
    ).group_by(measurement.station).order_by(func.count().desc())

    # Execute the query and fetch the results
    active_stations_results = active_stations_query.all()

    # Calculate the date 1 year ago from the last data point in the database
    last_date = session.query(func.max(measurement.date)).filter(measurement.station == 'USC00519281').scalar()
    one_year_ago = dt.datetime.strptime(last_date, '%Y-%m-%d') - dt.timedelta(days=365)

    # Query temperature observations for the last 12 months from the most active station
    results = session.query(measurement.date, measurement.tobs).\
        filter(measurement.station == 'USC00519281').\
        filter(measurement.date >= one_year_ago).all()

    # Convert the query results to a list of dictionaries
    tobs_data = [{'date': date, 'tobs': tobs} for date, tobs in results]

    return jsonify(tobs_data)

# Query the dates and temperature observations of the most-active station for the previous year of data. Return a JSON list of temperature observations for the previous year.
@app.route('/api/v1.0/<start>')
def start_date_stats(start):
    results = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= start).all()

    # Convert the query results to a list of dictionaries
    temperature_stats = [{'min temp': result[0], 'avg temp': result[1], 'max temp': result[2]} for result in results]

    return jsonify(temperature_stats)

# Return a JSON list of the minimum temperature, the average temperature, and the maximum temperature for a specified start or start-end range. For a specified start, calculate `TMIN`, `TAVG`, and `TMAX` for all the dates greater than or equal to the start date. For a specified start date and end date, calculate `TMIN`, `TAVG`, and `TMAX` for the dates from the start date to the end date, inclusive.
@app.route('/api/v1.0/<start>/<end>')
def start_end_date_stats(start, end):
    # Query TMIN, TAVG, and TMAX for the dates from start date to end date, inclusive
    results = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= start).\
        filter(measurement.date <= end).all()

    # Convert the query results to a list of dictionaries
    temperature_stats = [{'TMIN': result[0], 'TAVG': result[1], 'TMAX': result[2]} for result in results]

    return jsonify(temperature_stats)


if __name__ == '__main__':
    app.run(debug=True)