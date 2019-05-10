#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

import sys
import threading
import uuid

import time
from flask import Flask, render_template, Response, jsonify, send_file, abort
import logging
import paho.mqtt.client as mqtt #import the client1
from flask_socketio import SocketIO, join_room, leave_room
import redis

from autopial_lib.config_driver import ConfigFile

logger = logging.getLogger("sibus-server")
logger.setLevel(logging.DEBUG)
steam_handler = logging.StreamHandler()
stream_formatter = logging.Formatter('%(asctime)s|%(levelname)08s | %(message)s')
steam_handler.setFormatter(stream_formatter)
logger.addHandler(steam_handler)

redis_conn = None
supervisor_url = None

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
    except BaseException as e:
        logger.error("Invalid config file: {}".format(e))
        sys.exit(1)

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

    socketio.run(app, host="0.0.0.0", debug=True)

    mqtt_client.loop_stop()
