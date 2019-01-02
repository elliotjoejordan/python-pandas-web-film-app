import flask as fl
import jinja2
import numpy as np
import pandas as pd
from scipy.sparse.linalg import svds
import time

app = fl.Flask(__name__)

#######################################################################

# Movie rating recomendations functionality


# Maintains 2 tables
# ratings data containing UserID, MovieID and rating
# movie data containing MovieID, Movie_title and genres
ratings_data = pd.read_csv("ml-latest-small/ratings.csv")
movie_names = pd.read_csv("ml-latest-small/movies.csv")
users_data = pd.read_csv("ml-latest-small/users.csv")


def matrix_factorisation():
    ratings_data = pd.read_csv("ml-latest-small/ratings.csv")

    # Creates a matrix of users and movie ratings
    user_movie_rating = ratings_data.pivot_table(index='userId', columns='movieId', values='rating').fillna(0)
    # Creates a matrix for all user ratings then performs SVM to get the matrices U, sigma and Vt
    R = user_movie_rating.as_matrix()
    user_ratings_mean = np.mean(R, axis=1)
    R_demeaned = R - user_ratings_mean.reshape(-1, 1)
    U, sigma, Vt = svd(R_demeaned)
    all_user_predicted_ratings = np.dot(np.dot(U, sigma), Vt) + user_ratings_mean.reshape(-1, 1)
    predictions = pd.DataFrame(all_user_predicted_ratings, columns=user_movie_rating.columns)
    return predictions


def svd(R_demeaned):
    # Splits a demeaned matrix into U, sigma, Vt
    U, sigma, Vt = svds(R_demeaned, k=50)
    sigma = np.diag(sigma)
    return U, sigma, Vt


def makeRecommendation(userID):
    # Gets predictions for a user and returns a table of top recommended films for the user
    predictions = matrix_factorisation()
    user_predictions = predictions.iloc[userID - 1].sort_values(ascending=False)
    original_ratings = ratings_data[ratings_data.userId == (userID)]
    user_full = (original_ratings.merge(movie_names, how='left', left_on='movieId', right_on='movieId'))

    recommendations = (movie_names[~movie_names['movieId'].isin(user_full['movieId'])].
                       merge(pd.DataFrame(user_predictions).reset_index(), how='left',
                             left_on='movieId',
                             right_on='movieId').
                       rename(columns={userID - 1: 'predictions'}).
                       sort_values('predictions', ascending=False).
                       iloc[:5, :-1]
                       )

    return recommendations


#######################################################################

# Server functionality

userId = 0
fname = ""


@app.route("/")
def output():
    return fl.render_template('login.html')


@app.route('/home', methods=['POST'])
def login():
    # read json + reply
    data = fl.request.form['Username']
    password = fl.request.form['password']
    user = users_data.loc[users_data['username'] == data]
    if not user.empty:
        if user.iloc[0]['password'] == password:
            global fname
            global userId
            name = user.iloc[0]["name"]
            fname = name.split(" ")[0]
            userId = user.iloc[0]["userId"]
            listFilms = list(movie_names['title'])




            try:

                table = makeRecommendation(userId)
                del table['movieId']
                table = table.reset_index()
                del table['index']

                # Get personal stats
                original_ratings = (ratings_data[ratings_data.userId == (userId)]).sort_values(by=["rating"],
                                                                                               ascending=False)
                ratingsNumber = len(list(original_ratings['rating']))
                movieID = original_ratings.iloc[0]['movieId']
                movieToCheck = movie_names[movie_names['movieId'] == movieID]
                favouriteMovie = movieToCheck.iloc[0]['title']
                listedGenres = list(table['genres'])
                genres = {}
                for sublist in listedGenres:
                    listed = sublist.split("|")
                    for i in listed:
                        if i in genres:
                            genres[i] += 1
                        else:
                            genres[i] = 1
                current = {"genre": "", "number": 0}
                for i in genres:
                    if genres[i] > current["number"]:
                        current['genre'] = i
                        current['number'] = genres[i]
                genre = current['genre']



                return fl.render_template('index.html', name=fname, tables=[table.to_html(classes='data')],
                                          titles=table.columns.values, option_list=listFilms, genre=genre, reviews=ratingsNumber, favourite=favouriteMovie)
            except:
                return fl.render_template('index.html', name=fname, option_list=listFilms, genre="n/a", reviews="n/a", favourite="n/a")
        else:
            return fl.render_template('login.html')
    else:
        return fl.render_template('login.html')


@app.route("/create")
def loadCreate():
    listFilms = list(movie_names['title'])
    return fl.render_template('create.html', option_list=listFilms)


@app.route("/new", methods=['POST'])
def attempt():
    data = fl.request.form['Username']
    user = users_data.loc[users_data['username'] == data]
    if user.empty:
        # Create the new user
        userId = users_data.shape[0] + 1
        username = data
        name = fl.request.form['Name']
        password = fl.request.form['password']
        users_data.loc[userId - 1] = [userId, name, username, password]
        file = open("ml-latest-small/users.csv", "a+")
        file.write(str(userId) + "," + name + "," + username + "," + password + "\n")
        file.close()

        # Add their first review

        film = fl.request.form['filmName']
        filmFull = movie_names.loc[movie_names['title'] == film]
        rating = fl.request.form['rating']
        timeNow = time.time()
        timeNow = int(round(timeNow))
        movieId = filmFull.iloc[0]['movieId']
        indexing = ratings_data.shape[0]
        ratings_data.loc[indexing] = [userId, movieId, rating, timeNow]
        file = open("ml-latest-small/ratings.csv", "a+")
        file.write(str(userId) + "," + str(movieId) + "," + str(rating) + "," + str(timeNow) + "\n")
        file.close()

        return fl.render_template('login.html')
    else:
        return fl.render_template('create.html')


@app.route("/add", methods=['POST'])
def reload():
    film = fl.request.form['filmName']
    global userId
    global fname
    global ratings_data
    if len(film) > 0:
        filmFull = movie_names.loc[movie_names['title'] == film]
        rating = fl.request.form['rating']
        timeNow = time.time()
        timeNow = int(round(timeNow))
        movieId = filmFull.iloc[0]['movieId']
        indexing = ratings_data.shape[0]
        ratings_data.loc[indexing] = [userId, movieId, rating, timeNow]
        file = open("ml-latest-small/ratings.csv", "a+")
        file.write(str(userId) + "," + str(movieId) + "," + str(rating) + "," + str(timeNow) + "\n")
        file.close()
    table = makeRecommendation(int(userId))
    del table['movieId']
    table = table.reset_index()
    del table['index']
    listFilms = list(movie_names['title'])

    # Get personal stats
    ratings_data = pd.read_csv("ml-latest-small/ratings.csv")
    original_ratings = (ratings_data[ratings_data.userId == (userId)]).sort_values(by=["rating"], ascending=False)
    ratingsNumber = len(list(original_ratings['rating']))
    movieID = original_ratings.iloc[0]['movieId']
    movieToCheck = movie_names[movie_names['movieId'] == movieID]
    favouriteMovie = movieToCheck.iloc[0]['title']
    listedGenres = list(table['genres'])
    genres = {}
    for sublist in listedGenres:
        listed = sublist.split("|")
        for i in listed:
            if i in genres:
                genres[i] += 1
            else:
                genres[i] = 1
    current = {"genre": "", "number": 0}
    for i in genres:
        if genres[i] > current["number"]:
            current['genre'] = i
            current['number'] = genres[i]
    genre = current['genre']


    return fl.render_template('index.html', name=fname, tables=[table.to_html(classes='data')],
                              titles=table.columns.values, option_list=listFilms, genre=genre, favourite=favouriteMovie, reviews=ratingsNumber)


@app.route("/account")
def account():
    global userId
    global fname
    original_ratings = ratings_data[ratings_data.userId == (userId)]
    movieIds = list(original_ratings['movieId'])
    movies = pd.DataFrame(columns=['Title', 'Rating'])
    for movieId in movieIds:
        filmFull = movie_names.loc[movie_names['movieId'] == movieId]
        movieName = filmFull.iloc[0]['title']
        ratingFull = original_ratings.loc[original_ratings['movieId'] == movieId]
        movieRating = ratingFull.iloc[0]['rating']
        index = movies.shape[0]
        movies.loc[index] = [movieName, movieRating]
    movies = movies.sort_values(by=['Rating'], ascending=False)
    movies = movies.reset_index()
    del movies['index']
    return fl.render_template('account.html', name=fname, tables=[movies.to_html(classes='data')],
                              titles=movies.columns.values)


@app.route("/return")
def back():
    global userId
    global fname
    table = makeRecommendation(userId)
    del table['movieId']
    table = table.reset_index()
    del table['index']
    listFilms = list(movie_names['title'])

    # Get personal stats
    original_ratings = (ratings_data[ratings_data.userId == (userId)]).sort_values(by=["rating"], ascending=False)
    ratingsNumber = len(list(original_ratings['rating']))
    movieID = original_ratings.iloc[0]['movieId']
    movieToCheck = movie_names[movie_names['movieId'] == movieID]
    favouriteMovie = movieToCheck.iloc[0]['title']
    listedGenres = list(table['genres'])
    genres = {}
    for sublist in listedGenres:
        listed = sublist.split("|")
        for i in listed:
            if i in genres:
                genres[i] += 1
            else:
                genres[i] = 1
    current = {"genre":"", "number":0}
    for i in genres:
        if genres[i] > current["number"]:
            current['genre'] = i
            current['number'] = genres[i]
    genre = current['genre']

    return fl.render_template('index.html', name=fname, tables=[table.to_html(classes='data')],
                              titles=table.columns.values, option_list=listFilms, genre=genre, reviews=ratingsNumber, favourite=favouriteMovie)


if __name__ == "__main__":
    app.run()
