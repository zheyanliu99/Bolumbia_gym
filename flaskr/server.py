import os
from flask import Flask, request, render_template, g, redirect, Response


app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    # a default secret that should be overridden by instance config
    SECRET_KEY="dev",
    # store the database in the instance folder
    DATABASE="postgresql://zl3119:1947@w4111.cisxo09blonu.us-east-1.rds.amazonaws.com/proj1part2",
)

import auth
import routine
import event
import core
import error_handler
import appointment
import userprofile
import post
import admin
import QA

app.register_blueprint(auth.bp)
app.register_blueprint(routine.bp)
app.register_blueprint(core.bp)
app.register_blueprint(error_handler.bp)
app.register_blueprint(event.bp)
app.register_blueprint(appointment.bp)
app.register_blueprint(userprofile.bp)
app.register_blueprint(post.bp)
app.register_blueprint(admin.bp)
app.register_blueprint(QA.bp)


if __name__ == "__main__":
    import click

    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):


        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


    run()