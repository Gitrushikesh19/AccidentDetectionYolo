# AccidentDetectionYolo
A compact end-to-end prototype that detects road accidents from images (YOLOv8), determines severity, and automatically alerts responders by sending SMS and browser push notifications. The stack couples a Python inference pipeline with a Node.js real-time server + web UI to record incidents, show them on a live map, and persist them for follow-up.

# What the project offers
Traffic accidents require rapid response. This project demonstrates a lightweight, automatable pipeline that:
- Detects whether an image contains an accident and estimates severity (none / minor / moderate / severe).
- Identifies which camera/device produced the image (device id embedded in filename).
- Looks up the device’s latest GPS coordinates reported to the server.
- Sends immediate alerts (SMS + web push) with a timestamp, severity and map link so responders can act fast.
- Provides the most recent information of any accident captured by the device and severs with a link that directs them to the maps.

# Areas of improvement and parts to be implemented
- Use of detection transforms for more contexual understanding of the frames and minimizing possibility of capturing false positive instances.
- Accept and store evidence images on the server (or cloud storage) and include public URLs in SMS.
- Add user authentication + roles (admin, first responder, and other official users) to access this information and not be spread to public.
- Replace minimal front-end with a React dashboard which consists of incident details, responder details, and overall incident took place in a particular time period and it's visuals.

It still is in prototype stage!
