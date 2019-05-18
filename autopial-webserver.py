#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

import sys
import threading
import uuid

import time
from flask import Flask, render_template, Response, jsonify, send_file, abort, g
import logging
import paho.mqtt.client as mqtt #import the client1
from flask_socketio import SocketIO, join_room, leave_room
import redis

from autopial_lib.config_driver import ConfigFile
from autopial_lib.database_driver import DatabaseDriver

logger = logging.getLogger("sibus-server")
logger.setLevel(logging.DEBUG)
steam_handler = logging.StreamHandler()
stream_formatter = logging.Formatter('%(asctime)s|%(levelname)08s | %(message)s')
steam_handler.setFormatter(stream_formatter)
logger.addHandler(steam_handler)

redis_conn = None
supervisor_url = None
db = None

app = Flask(__name__)
socketio = SocketIO(app)

@app.route("/")
@app.route("/index.html")
def index():
    return render_template('index.html', device_list=device_list())

@app.route("/camera_live.html")
def camera_live_html():
    return render_template('camera_live.html', device_list=device_list())

@app.route("/camera_timelap.html")
def camera_timelap_html():
    return render_template('camera_timelap.html', device_list=device_list())

@app.route("/timelaps.html")
def timelaps_page():
    return render_template('timelaps.html', device_list=device_list())

@app.route("/system_status.html")
def system_status_html():
    return render_template('system_status.html', device_list=device_list())

@app.route("/gps_info.html")
def gps_info_html():
    return render_template('gps_info.html', device_list=device_list())

@app.route("/supervisor.html")
def supervisor_html():
    return render_template('supervisor.html', device_list=device_list(), supervisor_url=supervisor_url)

@app.route("/session_history.html")
def session_history_html():
    sessions = get_db().get_all_sessions()
    return render_template('session_history.html', device_list=device_list(), sessions = sessions)

@app.route("/session_viewer.html")
@app.route("/session_viewer.html/<autopial_id>")
def session_viewer_html(autopial_id=None):
    session = get_db().get_session(autopial_id)
    if session is not None:
        return render_template('session_viewer.html', device_list=device_list(), session = session)
    else:
        abort(404)

@app.route("/session/<autopial_id>/gps")
def session_gps_json(autopial_id=None):
    gps_locations = get_db().get_gps_locations(autopial_id)
    if gps_locations is not None:
        return jsonify(gps_locations)
    else:
        abort(404)

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'db_session'):
        logger.info("Connecting to database: {}".format(database_path))
        g.db_session = DatabaseDriver(database=database_path, logger=logger)
    return g.db_session

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    #if hasattr(g, 'db_session'):
    #    g.db_session.close()
    pass

def emit_all():
    logger.info("Emitting all topics on SocketIO")
    time.sleep(2)
    for key in redis_conn.scan_iter():
        try:
            payload_str = redis_conn.get(key)
        except:
            continue
        autopial_uid, key = key.split("/", 1)
        payload = json.loads(payload_str)
        #logger.info(" + {} : {}".format(key, payload_str))
        logger.info("Forward MQTT message to SocketIO: {} = {}".format(key, payload_str))
        socketio.emit(key, payload, namespace="/"+autopial_uid)
        pass

def device_list():
    device_list = redis_conn.smembers("autopial_uids")
    tmp = []
    for dev in device_list:
        if(dev.startswith("{")):
            tmp.append(json.loads(dev))
    return tmp

@socketio.on('connect')
def client_connected():
    logger.debug("New client connected on SocketIO")
    #emit_all()

@socketio.on('refresh')
def refresh_socketio():
    emit_all()

class SimpleThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._stopevent = threading.Event( )

    def run(self):
        while not self._stopevent.isSet():
            pass

    def stop(self):
        self._stopevent.set( )

def on_message(client, userdata, message):
    payload_str = message.payload.decode("utf-8")
    payload = json.loads(payload_str)

    autopial_device_name = payload["autopial"]["device_name"]
    autopial_device_uid = payload["autopial"]["device_uid"]
    autopial_process_name = payload["autopial"]["process_name"]
    autopial_worker_name = payload["autopial"]["worker_name"]

    redis_topic = "{}/{}".format(autopial_device_uid, message.topic)
    redis_conn.set(redis_topic, payload_str)
    redis_conn.sadd("autopial_uids", json.dumps({
        "autopial_uid": autopial_device_uid,
    }))

    logger.info("Forward MQTT message to SocketIO: {} = {}".format(message.topic, payload_str))
    socketio.emit(message.topic, payload, namespace="/"+autopial_device_uid)
    pass

if __name__ == '__main__':
    cfg = ConfigFile("autopial-webserver.cfg", logger=logger)
    try:
        supervisor_url = cfg.get("supervisor", "url")
        database_path = cfg.get("database", "path")
    except BaseException as e:
        logger.error("Invalid config file: {}".format(e))
        sys.exit(1)

    try:
        redis_conn = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    except redis.exceptions.ConnectionError as e:
        logger.error("Connection to local redis refused. Redis installed ? (sudo apt install redis-server)")
        sys.exit(1)

    broker_address = "localhost"
    mqtt_client = mqtt.Client("autopial-webserver-{}".format(uuid.uuid4().hex))
    mqtt_client.on_message = on_message
    try:
        mqtt_client.connect(broker_address)
        mqtt_client.loop_start()
        mqtt_client.subscribe("autopial/#", qos=1)
    except Exception as e:
        logger.error("Connection to MQTT broker {} error ! ({})".format(broker_address, e))
        sys.exit(1)

    socketio.run(app, host="0.0.0.0", debug=False)

    mqtt_client.loop_stop()
