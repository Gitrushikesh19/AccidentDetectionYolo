const socket = io();

// fetch device_id from the server (hostname)
async function getDeviceId() {
  try{
    const res = await fetch('/api/device-id');
    if (!res.ok) throw new Error('no device_id');
    const j = await res.json();
    if (j && j.device_id) return j.device_id;
  } catch (e) {
    console.warn('Device id fetch failed:', e);
  }
  const KEY = 'accident_device_id';
  let id = localStorage.getItem(KEY);
  if (!id) {
    id = 'dev-' + Date.now().toString(36);
    localStorage.setItem(KEY, id);
  }
  return id;
}

(async () => {
  const DEVICE_ID = await getDeviceId();

  const map = L.map('map').setView([0, 0], 2);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{
    attribution: 'Accident Location'
  }).addTo(map);

  let marker = null;
  let accuracyCircle = null;
  let firstFix = true;

  if ('geolocation' in navigator) {
    navigator.geolocation.watchPosition(
      (position) => {
        const {latitude, longitude, accuracy} = position.coords;

        socket.emit('send-location', {
          device_id: DEVICE_ID,
          latitude,
          longitude,
          accuracy,
          timestamp: new Date(position.timestamp).toISOString()
        });

        const latlng = [latitude, longitude];
        if (firstFix) {
          map.setView(latlng, 15);
          firstFix = false;
        }

        if (!marker) {
          marker = L.marker(latlng).addTo(map);
        } else {
          marker.setLatLng(latlng);
        }

        if (accuracy != null) {
          if (!accuracyCircle) {
            accuracyCircle = L.circle(latlng, {radius: accuracy}).addTo(map);
          } else {
            accuracyCircle.setLatLng(latlng);
            accuracyCircle.setRadius(accuracy);
          }
        }
      },
      (err) => {
        console.error('Geolocation error', err);
      },
      {enableHighAccuracy: true, maximumAge: 0, timeout: 10000}
    );
  } else {
    console.error('Geolocation not supported');
  }
})();
