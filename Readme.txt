Readme.txt

To use the web application, first ensure numpy has been installed for the latest version of python (pip3 install numpy).

To launch the server, navigate to the directory in terminal, and enter 'python3 server.py'
This will start the server, which can then be accessed by entering the url printed in terminal in any search engine.

System Features:

- Login page and create new account
- User profiles include name, username and password for personalisation
- Home page includes table of 5 recommendations based on matching algorithm, add new review, and personalised stats for the user
- account page, which shows all past reviews


The algorithm to recommend films to users uses matrix factorization to make choices. It breaks the matrix of users and movie ratings down into sub-matrices, and takes the 'closest' 50 to be considered significantly similar to the user - and reflect their habits in ways that can be used to predict which movies the user might watch based on movies other users watched. The system returns 5 films that are most highly rated for that user, which they've not watched.

The recommendation system implemented is robust and effective in its predictions, performing well on large data sets (such as a large database of movie reviews) and is an effective way to make recommendations.

The app is also personalised with user messages and stats to improve engagement. The design is user-friendly and easy to navigate, as well as being visually guiding so that the user can see features clearly and utilize the functionality.
