i. Download the GeoJSON file to `data/GBR_GeoJSON.json`.

ii. Use config.cfg to run the application which is similar to config.example.cfg but with valid credentials.

------------------

# Sentiment analysis
Combined visualisation, loads files off of the Mongo-DB server How to set up:

* Clone repository
* Include GeoJSON.json file from Google Drive inside the /data/ folder
* Set up MongoDB [https://www.digitalocean.com/community/tutorials/how-to-install-mongodb-on-ubuntu-16-04](https://www.digitalocean.com/community/tutorials/how-to-install-mongodb-on-ubuntu-16-04)
* `git checkout origin/mongodb`
* `pip3 install -r requirements.txt`
* `python3 main.py`


Because not every interval has data populating it, the scrollbar needs to be limited to files which do have data. Due to current bugs, as a temporary fix, a section of the code is commented inside templates/application.html.

* uncomment the code
* open <HOST>/application
* inspect element
* find the largest value of "minval" which is displayed
* comment the code again, and replace "minval" in the line beneath it with that value (+ 1)


## To Do:

* Stop the scrollbar from reloading the whole HTML page
* Add Stream Graph
* Overlay all svg elements to make a clean inteface - or use Bootstrap layout options
* Improve csv parsing speed for the map update
* Add country divide for the map
* Split up HTML and Javascript code files
