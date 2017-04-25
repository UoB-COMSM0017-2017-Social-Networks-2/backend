
  var width = screen.width * 0.6;
  height = screen.height * 0.65;

  // Create an SVG element in which the map/everything will go - select the #map column and append an svg to it
  var svg = d3.select("#map")
    .append("svg")
    //.attr("preserveAspectRatio", "xMinYMin meet")
    //.attr("viewBox", "0 0 " + width + " " + height)
    //.classed("svg-content-responsive", true) // Responsive to window sizing
    .attr("width", width)
    .attr("height", height)
    .on("click", stopped, true);
      
    active = d3.select(null);
    
  // Create a rectangle element behind the map to allow resetting the map
  svg.append("rect")
    .attr("class", "background")
    .attr("width", "100%")
    .attr("height", "100%")
    .on("click", reset);

  var map_scale = 2500;
  if(screen.width < 600){
    map_scale = 2300;
  }
  // Create the albers projection (to center the UK map correctly)
  var albersProjection = d3.geo.albers()
    .center([4, 55.4]) // UK is [0, 55.4]
    .rotate([4.4, 0])
    .parallels([50, 60])
    .scale(map_scale)
    .translate([width / 2, height / 2]);
    
  // Create a function geoPath - it takes a GeoJSON feature and returns SVG path data (SVG path = a shape)
  var geoPath = d3.geo.path()
    .projection(albersProjection);

  // Create a group to handle all svg elements simultaneously
  var g = svg.append( "g" );
 
    
  // Create a function which returns a colour based on sentiment values
  var color = d3.scale.threshold()
    .domain([-0.66, -0.33, 0.33, 0.66, 1])
    .range(["#FF0033", "#FF6000", "#FFFF00", "#B0FF00", "#80FF00", "#00FF00"]);
    
  // Queue allows handling of multiple files within the same function ("ready" - below)
  queue()
    .defer(d3.json, "static/mapdata/GBR_GeoJSON.json")
    .defer(d3.csv, "static/mapdata/MapData1.csv")
    .await(ready);

  // Display the map  
  function ready(error, UK_json, MapData) {
    if (error) throw error;
    
    var sentimentById = {}; // Array stores sentiment data
    MapData.forEach(function(d) { sentimentById[d.id] = 0/*+d.sentiment*/; }); // Bind the sentiment data from MapData to sentimentById

    g.selectAll( "path" )   // Select all SVG path elements - since the elements don't exist yet, they are created on the fly.
    .data( UK_json.features ) // Binds the geoJSON data to the page elements 
    .enter()          // Creates a new element
    .append( "path" )
    .attr( "d", geoPath )   // For SVGs - d defines the coordinates of a path. geoPath is a function which returns an SVG path
    .attr("class", "feature") // For CSS click and mouseover styling
    .attr("fill", function(d,i) { return color(sentimentById[i+1]); })  // Paint region (cf color function)
    .on("click", clicked)   // Zoom on click (cf clicked function)
    .on("mouseover", function(d,i){return tooltip.style("visibility", "visible"), 
                     tooltip.text(UK_json.features[i].properties.NAME_2 + ": " + sentimentById[i+1]);}) // Show region tooltip 
    .on("mousemove", function(){return tooltip.style("top", (d3.event.pageY-10)+"px").style("left",(d3.event.pageX+10)+"px");}) // Position of the tooltip
    .on("mouseout", function(){return tooltip.style("visibility", "hidden");}); // Hide tooltip
  };
  
  // button selection
  d3.selectAll(".btn-default").on("click", function() {
    console.log(this.id)
    console.log("hello")
    d3.csv("static/mapdata/MapData2.csv", function(error, MapData) {
      if (error) throw error;
    
      var sentimentById = {}; // Array stores sentiment data
      MapData.forEach(function(d) { sentimentById[d.id] = +d.sentiment; }); // Bind the sentiment data from MapData to sentimentById
      
      g.selectAll( "path" )
      .attr("fill", function(d,i) { return color(sentimentById[i+1]); });  // Paint region (cf color function)
    });
  });

  
  // Add zoom functionality
  var zoom = d3.behavior.zoom()
    .translate([0, 0])
    .scale(1)
    .scaleExtent([1, 8])
    .on("zoom", zoomed);  

  svg
    .call(zoom) // delete this line to disable free zooming
    .call(zoom.event);

  // Zoom on click
  function clicked(d) {
    if (active.node() === this) return reset();
    active.classed("active", false);
    active = d3.select(this).classed("active", true);

    var bounds = geoPath.bounds(d),
      dx = bounds[1][0] - bounds[0][0],
      dy = bounds[1][1] - bounds[0][1],
      x = (bounds[0][0] + bounds[1][0]) / 2,
      y = (bounds[0][1] + bounds[1][1]) / 2,
      scale = Math.max(1, Math.min(8, 0.9 / Math.max(dx / width, dy / height))),
      translate = [width / 2 - scale * x, height / 2 - scale * y];

    svg.transition()
      .duration(750)
      .call(zoom.translate(translate).scale(scale).event)
  }
  
  // Zoomed function
  function zoomed() {
    g.style("stroke-width", 1.5 / d3.event.scale + "px");
    g.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
  }
  
  // To reset the map to fullscreen
  function reset() {
    active.classed("active", false);
    active = d3.select(null);

    svg.transition()
      .duration(750)
      .call(zoom.translate([0, 0]).scale(1).event);
  }
  
  // If the drag behavior prevents the default click,
  // also stop propagation so we don’t click-to-zoom.
  function stopped() {
    if (d3.event.defaultPrevented) d3.event.stopPropagation();
  }

      // On mouseover tooltip
      var tooltip = d3.select("body")
        .append("div")
        .style("position", "absolute")
        .style("z-index", "10")
        .style("visibility", "hidden");
  
  // Update Map data
  var data_id = 1;
  function updateMap(){
      console.log(decodeURIComponent(location.hash));
      topic_id=decodeURIComponent(location.hash).split("==").shift().substring(1);
      interval_id = decodeURIComponent(location.hash).split("==").pop();
      topic_id = topic_id.replace("#", "%23");
      console.log(topic_id);
      console.log(interval_id);
      mapdata_url = "/topic/"+topic_id+"/interval/"+interval_id+".csv"
      
      d3.csv(mapdata_url, function(error, MapData) {
        if (error) throw error;
      
        var sentimentById = {}; // Array stores sentiment data
        MapData.forEach(function(d) { sentimentById[d.Region_ID.substring(2)] = +d.Average_sentiment; }); // Bind the sentiment data from MapData to sentimentById
        
        g.selectAll( "path" )
        .attr("fill", function(d,i) { return color(sentimentById[i+1]); });  // Paint region (cf color function)
      });

  };
  

function timeConverter(UNIX_timestamp){
  var a = new Date(UNIX_timestamp * 1000);
  var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var year = a.getFullYear();
  var month = months[a.getMonth()];
  var date = a.getDate();
  var hour = a.getHours();
  var min = a.getMinutes();
  var sec = a.getSeconds();
  var time = date + ' ' + month + ' ' + year + ' ' + hour + ':' + min + ':' + sec ;
  return time;
}

  $(window).on('hashchange', updateMap)
