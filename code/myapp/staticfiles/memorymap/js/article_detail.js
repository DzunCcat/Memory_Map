'use strict';

{
  const LIMIT = 30; // 移動回数の上限値
  const START_LAT_LNG = { lat: {{lat}}, lng: {{lng}} }; // 開始地点の緯度、経度
  const START_HEADING = 180; // 開始時の方角

  function initMap() {
      const map = new google.maps.Map(document.getElementById("map"), {
          center: START_LAT_LNG,
          zoom: 14,
      });
      const panorama = new google.maps.StreetViewPanorama(
          document.getElementById("pano"),
          {
              position: START_LAT_LNG,
              pov: {
                  heading: 34,
                  pitch: 10,
              },
          }
      );

      map.setStreetView(panorama);
  }

    window.initialize = initMap;
    
    // Add a declaration or statement here

  }
