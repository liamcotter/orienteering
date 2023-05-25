from requests import get
from datetime import datetime

from events import EventResult


class UserResult:
    def __init__(self, name: str, search_term: str):
        """
        Initialises the UserResult object

        Parameters:
            name (str): The name of the user
            search_term (str): The search string for the event name. It supports % as a wildcard character
        
        """
        self.name = name
        self.search_term = search_term
        self.event_results = {}
        self.compile_event_details()

    def compile_event_details(self) -> None:
        """Populates the attributes of the UserResult object"""

        name = self.name.replace(" ", "+")
        url = f"https://www.orienteering.ie/result2/?oaction=viewResults&league=&club=&map={self.search_term}&SMonth=&SYear=&FMonth=&FYear=&comptr={name}&start=0&XXX=Search"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            r = get(url, headers=headers)
        except Exception as e:
            raise Exception("Request Error", e)
        if r.status_code != 200:
            raise Exception("Request Error: status code ", r.status_code)

        table = r.text.split("tbody>")[1]
        rows = table.split("<tr>")[1:]
        for entry in rows:
            if "<td>" in entry and "DNF" not in entry:
                eventID = entry.split("moreResult&id=")[1].split('"')[0]
                result_info = entry.split("<td>")
                course, date, month = result_info[-2][:-5], result_info[1][:-5], result_info[2][:-5]
                time = result_info[-1].replace(" ", "").split("</td>")[0]
                time = int(time.split(":")[0])*60 + int(time.split(":")[1])
                date = datetime.strptime(f"{date} {month}", "%d %b")
                self.event_results[eventID] = EventResult(
                    eventID, course, time, date)
                self.event_results[eventID].add_event_data()
        if len(self.event_results) == 0:
            raise Exception("No Results Found")


person = "Liam Cotter"
search = "Fota%"
result = UserResult(person, search)