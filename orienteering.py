from requests import get
import pandas as pd
from io import StringIO
from datetime import datetime

class UserResult:
    def __init__(self, name : str, search_term : str):
        self.name = name
        self.search_term = search_term
        self.eventID = []
        self.eventResults = {}
        self.compile_event_details()

    def compile_event_details(self) -> None :
        """Populates the attributes of the UserResult object"""

        name = self.name.replace(" ", "+")
        url = f"https://www.orienteering.ie/result2/?oaction=viewResults&league=&club=&map={self.search_term}&SMonth=&SYear=&FMonth=&FYear=&comptr={name}&start=0&XXX=Search"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            r = get(url, headers=headers)
        except Exception as e:
            with open("logs.txt", "a") as f:
                f.write(f"{datetime.now()}\tSearch\t{e}\n")
            raise Exception("Request Failed")
        if r.status_code != 200:
            with open("logs.txt", "a") as f:
                f.write(f"{datetime.now()}\tSearch\t{r.status_code}\n")
            raise Exception("Request Failed")
        
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
                    self.eventResults[eventID] = EventResult(eventID, course, time, date)
                    self.eventResults[eventID].add_event_data()

class EventResult:
    def __init__(self, eventID : int, course : str, time : int, date : str):
        self.eventID = eventID
        self.course = course
        self.time = time
        self.winning_time = None
        self.distance = None
        self.date = date
        self.pace = None
        self.percent_behind = None
    
    def set_calculations(self) -> None:
        """Sets the pace, winning_time attribute"""
        if self.distance is None:
            self.pace = None
        else:
            self.pace = self.time / self.distance # assume seconds per KM
        self.percent_behind = 100* ((self.time / self.winning_time) -1)
    
    def add_event_data(self) -> None:
        """Adds the winning time and distance to the EventResult object"""
        df = get_df(self.eventID)
        relevant_data = df[df["Course"] == self.course]
        self.winning_time = get_best_time(relevant_data)
        self.distance = get_distance(relevant_data)
        self.set_calculations()

# eventID = 22733
def get_df(eventID : int) -> pd.DataFrame:
    """Fetches the results CSV"""

    url = f"https://www.orienteering.ie/results/files/{str(eventID)[:-2]}/{str(eventID)}.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = get(url, headers=headers)
    except Exception as e:
        with open("logs.txt", "a") as f:
            f.write(f"{datetime.now()}\tCSV\t{e}\n")
        raise Exception("Request Failed")
    if r.status_code != 200:
        with open("logs.txt", "a") as f:
            f.write(f"{datetime.now()}\CSV\t{r.status_code}\n")
        raise Exception("Request Failed")
    
    fixed_csv = r.text.replace("(may be more) ...", "(may be more) ...;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;")
    #with open("test.csv", "w") as f:
    #    f.write(fixed_csv)
    if "<title>" in fixed_csv:
        raise Exception("Request Failed")
    df = pd.read_csv(StringIO(fixed_csv), sep=";").dropna(axis=1, how="all")
    return df

def get_best_time(df : pd.DataFrame) -> int:
    """Gets the winning time on the course"""
    times = df["Time"].dropna()
    times_in_seconds = times.transform(lambda t: int(t.split(":")[0])*60 + int(t.split(":")[1]))
    winning_time = min(times_in_seconds)
    return winning_time

def get_distance(df : pd.DataFrame) -> float:
    """Gets the distance of the course"""
    km = ""
    if len(df["km"]) > 0:
        if float(df["km"].iloc[0]) == 0:
            km = None
        else:
            km = float(df["km"].iloc[0])
    return km

person = "Liam Cotter"
search = "Fota%"
res = UserResult(person, search)

# need to fix DNFs when finding best time