'use strict';

function initialize() {
  let panorama;
  let latitude = parseFloat(document.getElementById("street-view").getAttribute("data-latitude"));
  let longitude = parseFloat(document.getElementById("street-view").getAttribute("data-longitude"));

  let position = new google.maps.LatLng({ lat: latitude, lng: longitude });

  panorama = new google.maps.StreetViewPanorama(
    document.getElementById("street-view"),
    {
      position: position,
      pov: { heading: 165, pitch: 0 },
      zoom: 1,
    },
  );
}