const express = require('express');
const app = express();
const path = require('path');
require('dotenv').config({path: path.join(__dirname, '.env.local')});
const http = require('http');
const { Server } = require('socket.io');
const fs = require('fs');
const os = require('os');
const bodyParser = require('body-parser');
const { sendTwilioSms } = require('./twilio_util');
const { format } = require('util');

const server = http.createServer(app);
const io = new Server(server);

// static file -> public folder
app.use(express.static(path.join(__dirname, 'public')));
//JSON body parser
app.use(bodyParser.json({limit: '10mb'}));

const csv_dir = path.join(__dirname, 'logs');
const csv_file = path.join(csv_dir, 'device_locations.csv');
// const detection_log_file = path.join(csv_dir, 'detections.log');

// create csv header if missing
if (!fs.existsSync(csv_file)) {
  fs.writeFileSync(csv_file, 'device_id, timestamp_iso, latitude, longitide, accuracy\n', {encoding: 'utf8'});
}

const latestMap = {};

// socket.io connection handling
io.on('connection', (socket) =>{
  console.log('Client connected:', socket.id);

  socket.on('send-location', (payload) =>{
    try{
      const device_id = String(payload.device_id || 'unknown').replace(/[^a-zA-Z0-9_-]/g, "");
      const latitude = Number(payload.latitude);
      const longitude = Number(payload.longitude);
      const accuracy = (payload.accuracy == null) ? "" : Number(payload.accuracy);
      const timestamp = payload.timestamp ? String(payload.timestamp) : new Date().toISOString();

      if (Number.isFinite(latitude) && Number.isFinite(longitude) && latitude >= -90 && longitude >= -180 && longitude <= 180){
        latestMap[device_id] = {latitude, longitude, accuracy, timestamp};
        
        // append to csv
        const line = `${device_id}, ${timestamp}, ${latitude}, ${longitude}, ${accuracy}${os.EOL}`;
        fs.appendFile(csv_file, line, (err) =>{
          if (err){
            console.error('failed to write to CSV:', err);
            socket.emit('err', {message: 'Server write error'});
          } else {
            socket.emit('location-saved', {ok: true, timestamp});
          }
        });

        //notify any live map clients
        io.emit('location:update', {device_id, latitude, longitude, accuracy, timestamp});
      } else {
        console.warn('Invalid coords received, ignored:', payload);
      }
    } catch (e) {
      console.error('Error handling send-location:', e);
    }
  });

  socket.on('disconnect', () =>{
    console.log('Client disconnected:', socket_id);
  });
});

// HTTP: detection endpoint
app.post('/api/detection', async (req, res) =>{
  try{
    const body = req.body || {};
    const device_id = String(body.device_id || 'unknown');
    const severity = String(body.severity || 'unknown');
    const confidence = Number(body.confidence || body.conf || 0.0);
    const image_path = body.image_path || null;
    const timestamp = body.timestamp || new Date().toISOString();

    let lat = null, lon = null. acc = null;
    if (latestMap[device_id]){
      lat = latestMap[device_id].latitude;
      lon = latestMap[device_id].longitude;
      acc = latestMap[device_id].accuracy;
    } else {
      try {
      const csv = fs.readFileSync(csv_file, 'utf8');
      const lines = csv.trim().split(/\r?n/).slice(1).reverse();
      for (const line of lines) {
        const parts = line.split(',');
        if (parts[0] === device_id) {
          lat = parts[2];
          lon = parts[3];
          acc = parts[4];
          break;
        }
      }
    } catch (e) {
      console.warn('Could not read CSV:', e);
    }
  }

  const detectionLog = `${timestamp} | ${device_id} | ${severity} | ${confidence} | ${lat}, ${lon} | ${image_path}${os.EOL}`;
  fs.appendFileSync(detection_log_file, detectionLog, {encoding: 'utf8'});

  // compose sms body
  let smsBody = `SOS accident in the area\nDevice: ${device_id}\nTime: ${timestamp}\nSeverity: ${severity}\nConfidence: ${confidence.toFixed(2)}\n`;
  if (lat && lon) {
    smsBody += `location: ${lat}, ${lon}\nMap: https://www.google.com/maps/search/?api=1&query=${lat},${lon}\n`;
  } else {
    smsBody += `Location: Unknown\n`;
  }
  if (image_path) smsBody += `Evidence: ${image_path}\n`;

    const now = Date.now();
    let willSendSms = true;
    let cooldownReason = null;

    // global cooldown
    if (GLOBAL_SMS_COOLDOWN_MS > 0 && (now - lastGlobalSentAt < GLOBAL_SMS_COOLDOWN_MS)) {
      willSendSms = false;
      cooldownReason = `global cooldown (${GLOBAL_SMS_COOLDOWN_MS/1000}s)`;
    }

    // per-device cooldown
    if (willSendSms) {
      const lastSent = smsCooldownMap[device_id] || 0;
      if (now - lastSent < SMS_COOLDOWN_MS) {
        willSendSms = false;
        cooldownReason = `device cooldown (${SMS_COOLDOWN_MS/1000}s)`;
      }
    }

    if (willSendSms) {
      try {
        const twilioResp = await sendTwilioSms(smsBody);
        smsCooldownMap[device_id] = now;
        lastGlobalSentAt = now;
        io.emit('detection:alert', { device_id, severity, confidence, lat, lon, timestamp, sms_sent: true, twilio: !!twilioResp });
      } catch (e) {
        console.warn('Twilio send failed (logged):', e);
        io.emit('detection:alert', { device_id, severity, confidence, lat, lon, timestamp, sms_sent: false, error: String(e) });
      }
    } else {
      // log skipped sms
      fs.appendFileSync(detection_log_file, `${timestamp} | ${device_id} | SKIPPED_SMS (${cooldownReason}) | ${severity} | ${confidence} | ${lat},${lon} | ${image_path}${os.EOL}`, { encoding: 'utf8' });
      io.emit('detection:alert', { device_id, severity, confidence, lat, lon, timestamp, sms_sent: false, reason: cooldownReason });
    }

    res.json({ ok: true, device_id, lat, lon, sms_sent: willSendSms, reason: cooldownReason });
  } catch (e) {
    console.error('Detection endpoint error:', e);
    res.status(500).json({ error: 'server_error' });
  }
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => console.log(`Server listening on ${PORT}`));
