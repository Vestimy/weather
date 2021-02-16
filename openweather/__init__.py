import requests
import json
from datetime import datetime


class OpenWeather:
    """
    Документация OpenWeather.
    Call current weather data for one location
    By city name
    You can call by city name or city name, state code and country code. Please note that searching by states available only for the USA locations.

    q    -   required	City name, state code and country code divided by comma, use ISO 3166 country codes.
                You can specify the parameter not only in English. In this case, the API response should be returned in the same language as the 
                language of requested location name if the location is in our predefined list of more than 200,000 locations.

    appid -  required	Your unique API key (you can always find it on your account page under the "API key" tab)
    mode  -  optional	Response format. Possible values are xml and html. If you don't use the mode parameter format is JSON by default. Learn more
    units -  optional	Units of measurement. standard, metric and imperial units are available. If you do not use the units parameter, standard units will be applied by default. Learn more
    lang  -  optional	You can use this parameter to get the output in your language.

    Fields in API response

    coord
        coord.lon City geo location, longitude
        coord.lat City geo location, latitude
    weather (more info Weather condition codes)
        weather.id Weather condition id
        weather.main Group of weather parameters (Rain, Snow, Extreme etc.)
        weather.description Weather condition within the group. You can get the output in your language. Learn more
        weather.icon Weather icon id
    base Internal parameter
    main
        main.temp Temperature. Unit Default: Kelvin, Metric: Celsius, Imperial: Fahrenheit.
        main.feels_like Temperature. This temperature parameter accounts for the human perception of weather. Unit Default: Kelvin, Metric: Celsius, Imperial: Fahrenheit.
        main.pressure Atmospheric pressure (on the sea level, if there is no sea_level or grnd_level data), hPa
        main.humidity Humidity, %
        main.temp_min Minimum temperature at the moment. This is minimal currently observed temperature (within large megalopolises and urban areas). Unit Default: Kelvin, Metric: Celsius, Imperial: Fahrenheit.
        main.temp_max Maximum temperature at the moment. This is maximal currently observed temperature (within large megalopolises and urban areas). Unit Default: Kelvin, Metric: Celsius, Imperial: Fahrenheit.
        main.sea_level Atmospheric pressure on the sea level, hPa
        main.grnd_level Atmospheric pressure on the ground level, hPa
    wind
        wind.speed Wind speed. Unit Default: meter/sec, Metric: meter/sec, Imperial: miles/hour.
        wind.deg Wind direction, degrees (meteorological)
        wind.gust Wind gust. Unit Default: meter/sec, Metric: meter/sec, Imperial: miles/hour
    clouds
        clouds.all Cloudiness, %
    rain
        rain.1h Rain volume for the last 1 hour, mm
        rain.3h Rain volume for the last 3 hours, mm
    snow
        snow.1h Snow volume for the last 1 hour, mm
        snow.3h Snow volume for the last 3 hours, mm
    dt Time of data calculation, unix, UTC
    sys
        sys.type Internal parameter
        sys.id Internal parameter
        sys.message Internal parameter
        sys.country Country code (GB, JP etc.)
        sys.sunrise Sunrise time, unix, UTC
        sys.sunset Sunset time, unix, UTC
    timezone Shift in seconds from UTC
    id City ID
    name City name
    cod Internal parameter 
    """
    url = "http://api.openweathermap.org/data/2.5/weather"
    cache = {}

    def __init__(self, appid=None, db=None, model=None, url=None, units='metric', lang='ru'):
        self.is_url(url)
        self.params = {
            'appid': appid,
            'units': units,
            'lang': lang
        }
        self.db = db
        self.model = model

    def request(self, params):
        return requests.get(self.url, params=params)

    def is_api(self):
        if self.params.get('appid') is not None:
            return True

    def is_url(self, url):
        if url is not None:
            self.url = url

    def get_db(self, params):
        data = self.model.query.filter(self.model.city == params.get('q')).first()
        if data:
            if data.created_weather.strftime('%Y.%m.%d') != datetime.now().strftime('%Y.%m.%d'):
                return self.delete_db(data, params)
            return json.loads(data.json)
        return self.update_db(params)

    def delete_db(self,data, params):
        self.db.session.delete(data)
        self.db.session.commit()
        return self.update_db(params)

    def update_db(self, params):
        data = self.request(self.params).text
        mod = self.model(city=params.get('q'), json=data)
        self.db.session.add(mod)
        self.db.session.commit()
        return json.loads(data)

    def get(self, **kwargs):
        if self.is_api():
            for key, value in kwargs.items():
                self.params[key] = value
            if self.db is not None and self.model is not None:
                return self.get_db(self.params)
            if kwargs.get('q') in self.cache.keys():
                return self.cache.get(kwargs.get('q'))
            data = self.request(self.params)
            self.cache[kwargs.get('q')] = data
            return data.json()