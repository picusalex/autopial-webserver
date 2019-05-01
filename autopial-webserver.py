#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

import sys
import uuid

from flask import Flask, render_template, Response, jsonify, send_file, abort
import logging
import paho.mqtt.client as mqtt #import the client1
from flask_socketio import SocketIO
import redis

logger = logging.getLogger("sibus-server")
logger.setLevel(logging.DEBUG)
steam_handler = logging.StreamHandler()
stream_formatter = logging.Formatter('%(asctime)s|%(levelname)08s | %(message)s')
steam_handler.setFormatter(stream_formatter)
logger.addHandler(steam_handler)

redis_conn = None

app = Flask(__name__)
socketio = SocketIO(app)

@app.route("/")
@app.route("/index.html")
def index():
    return render_template('index.html')

@app.route("/camera_live.html")
def camera_live_html():
    return render_template('camera_live.html')

@app.route("/camera_timelap.html")
def camera_timelap_html():
    return render_template('camera_timelap.html')

@app.route("/timelaps.html")
def timelaps_page():
    return render_template('timelaps.html')

@app.route("/system_status.html")
def system_status_html():
    return render_template('system_status.html')

@app.route("/gps_info.html")
def gps_info_html():
    return render_template('gps_info.html')

@app.route("/supervisor.html")
def supervisor_html():
    return render_template('supervisor.html')

def emit_all():
    logger.info("Emitting all topics on SocketIO")
    for key in redis_conn.scan_iter():
        payload_str = redis_conn.get(key)
        payload = json.loads(payload_str)
        logger.info(" + {} : {}".format(key, payload_str))
        socketio.emit(key, payload)

@socketio.on('connect')
def client_connected():
    logger.debug("New client connected on SocketIO")
    emit_all()

def on_message(client, userdata, message):
    payload_str = message.payload.decode("utf-8")
    redis_conn.set(message.topic, payload_str)

    logger.info("Forward MQTT message to SocketIO: {} = {}".format(message.topic, payload_str))
    payload = json.loads(payload_str)
    socketio.emit(message.topic, payload)

if __name__ == '__main__':
    try:
        redis_conn = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    except redis.exceptions.ConnectionError as e:
        logger.error("Connection to redis refused. Redis installed ? (sudo apt install redis-server)")
        sys.exit(1)

    broker_address = "localhost"
    mqtt_client = mqtt.Client("sibus-server-{}".format(uuid.uuid4().hex))
    mqtt_client.on_message = on_message
    mqtt_client.connect(broker_address)
    mqtt_client.loop_start()
    mqtt_client.subscribe("autopial/#", qos=1)

    socketio.run(app, host="0.0.0.0")

    mqtt_client.loop_stop()
