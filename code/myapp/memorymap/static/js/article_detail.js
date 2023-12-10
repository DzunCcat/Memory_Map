

function initialize() {

  let panorama;

  let latitude = "{{ article.latitude }}";
  let longitude = "{{ article.longitude }}";

  panorama = new google.maps.StreetViewPanorama(
    document.getElementById("street-view"),
    {
      position: { lat: latitude, lng: longitude },
      pov: { heading: 165, pitch: 0 },
      zoom: 1,
    },
  );
}

window.initialize = initialize;