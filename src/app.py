import os
import threading

import flask


APP = flask.Flask(__name__)
METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")


@APP.route("/favicon.ico")
def favicon():
    return flask.send_from_directory(
        os.path.join(APP.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@APP.route("/", defaults={"path": ""}, methods=METHODS)
@APP.route("/<path:path>", methods=METHODS)
def catch_all(path):
    return flask.jsonify({"path": path})


if __name__ == "__main__":
    APP.run(host="0.0.0.0", port=15071, debug=True)
