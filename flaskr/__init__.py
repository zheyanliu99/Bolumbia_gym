import os

from flask import Flask


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # store the database in the instance folder
        DATABASE="postgresql://zl3119:1947@w4111.cisxo09blonu.us-east-1.rds.amazonaws.com/proj1part2",
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    # register the database commands
    from flaskr import db

    # db.init_app(app)

    # apply the blueprints to the app
    from flaskr import auth
    from flaskr import routine
    from flaskr import event
    from flaskr import core
    from flaskr import error_handler
    from flaskr import appointment
    from flaskr import userprofile
    from flaskr import post

    app.register_blueprint(auth.bp)
    app.register_blueprint(routine.bp)
    app.register_blueprint(core.bp)
    app.register_blueprint(error_handler.bp)
    app.register_blueprint(event.bp)
    app.register_blueprint(appointment.bp)
    app.register_blueprint(userprofile.bp)
    app.register_blueprint(post.bp)

    # make url_for('index') == url_for('blog.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    # app.add_url_rule("/", endpoint="index")

    return app
