import requests
import json
import re

class DaftScrapper:
    @classmethod
    def daft_scrap(cls, price: int):
        url = "https://www.daft.ie/property-for-rent/galway-city?rentalPrice_to=" + str(price)
        response = requests.get(url)
        regex = "\{\".*\"\:\{.*\:.*\}"
        json_content = re.search(regex, response.text)
        json_text = json_content.group()
        data = json.loads(json_text)
        homes = data["props"]["pageProps"]["listings"]

        home_list = []
        for home in homes:
            home_dict = {
                "id": home["listing"]["id"],
                "title": home["listing"]["title"],
                "price": home["listing"]["price"],
                "url": "https://www.daft.ie/" + home["listing"]["seoFriendlyPath"]
            }
            home_list.append(home_dict)
        return home_list
