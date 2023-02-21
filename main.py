import os
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

API_KEY = "719c1ea10573867578dc9ebf2a467ee8"
API_SEARCH_MOVIES_LIST_ENDPOINT = "https://api.themoviedb.org/3/search/movie"
API_SEARCH_MOVIE_ENDPOINT = "https://api.themoviedb.org/3/movie/"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w300"

db = SQLAlchemy()
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db.init_app(app)
Bootstrap(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    title = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(250))
    img_url = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Book {self.title}>'


class UpdateForm(FlaskForm):
    new_rating = StringField(label="Your Rating Out of 10 e.g. 7.5", validators=[DataRequired()])
    new_review = StringField(label="Your review", validators=[DataRequired()])
    submit = SubmitField(label="Done")


class AddForm(FlaskForm):
    movie_to_add = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")


if not os.path.isfile('sqlite:///new-books-collection.db'):
    with app.app_context():
        db.create_all()


@app.route("/")
def home():
    all_movies = db.session.execute(db.select(Movie).order_by(Movie.rating.desc())).scalars().all()
    print(all_movies)
    for i in range(len(all_movies)):
        all_movies[i].ranking = i + 1
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit/<movie_title>", methods=["GET", "POST"])
def edit(movie_title):
    update_form = UpdateForm()
    if update_form.validate_on_submit():
        new_rating = update_form.new_rating.data
        new_review = update_form.new_review.data
        movie_to_update = Movie.query.filter_by(title=movie_title).first()
        movie_to_update.rating = new_rating
        movie_to_update.review = new_review
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=update_form)


@app.route("/delete/<movie_id>")
def delete(movie_id):
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    add_form = AddForm()
    if add_form.validate_on_submit():
        movie_title = add_form.movie_to_add.data
        return redirect(url_for('search', movie=movie_title))
    return render_template('add.html', form=add_form)


@app.route("/add/<movie_id>", methods=["GET", "POST"])
def add_movie(movie_id):
    parameters = {
        "api_key": API_KEY,
    }
    response = requests.get(url=f"{API_SEARCH_MOVIE_ENDPOINT}{movie_id}", params=parameters)
    response.raise_for_status()
    movie_data = response.json()
    print(movie_data['title'])
    with app.app_context():
        new_movie = Movie(title=movie_data["title"],
                          year=movie_data["release_date"].split("-")[0],
                          description=movie_data["overview"],
                          rating=None,
                          ranking=None,
                          review=None,
                          img_url=f"{MOVIE_DB_IMAGE_URL}{movie_data['poster_path']}"
                          )
        db.session.add(new_movie)
        db.session.commit()
    return redirect(url_for('edit', movie_title=movie_data['title']))


@app.route("/search/<movie>")
def search(movie):
    parameters = {
        "api_key": API_KEY,
        "query": movie,
    }
    response = requests.get(url=API_SEARCH_MOVIES_LIST_ENDPOINT, params=parameters)
    response.raise_for_status()
    movie_data = response.json()
    title_movie_list = [movie["original_title"] for movie in movie_data["results"]]
    year_movie_list = [movie["release_date"] for movie in movie_data["results"]]
    id_movie_list = [movie["id"] for movie in movie_data["results"]]
    zipped_list = list(zip(title_movie_list, year_movie_list, id_movie_list))
    return render_template('select.html', movie_info=zipped_list)


if __name__ == '__main__':
    app.run(debug=True)
