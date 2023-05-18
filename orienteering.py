from requests import get
import pandas as pd
from io import StringIO
from datetime import datetime

class UserResult:
    def __init__(self, name : str, search_term : str):
        self.name = name
        self.search_term = search_term
        self.eventID = []
        self.course = []
        self.times = []
        self.dates = []

class EventResult:
    def __init__(self, eventID : int, course : str, time : int, winning_time : int, distance : str, date : str):
        self.eventID = eventID
        self.course = course
        self.time = time
        self.winning_time = winning_time
        self.distance = distance
        self.date = date
        self.pace = None
        self.percent_behind = None
    
    def set_calculations(self):
        """Sets the pace, winning_time attribute"""
        if self.distance is None:
            self.pace = None
        else:
            self.pace = self.time / self.distance # assume seconds per KM
        self.percent_behind = 100* ((self.winning_time / self.time) -1)

# eventID = 22733
def get_df(eventID : int) -> pd.DataFrame:
    """Fetches the results CSV"""
    url = f"https://www.orienteering.ie/results/files/{str(eventID)[:3]}/{str(eventID)}.csv"
    print(url)
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = get(url, headers=headers)
    fixed_csv = r.text.replace("(may be more) ...", "(may be more) ...;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;")
    with open("test.csv", "w") as f:
        f.write(fixed_csv)
    df = pd.read_csv(StringIO(fixed_csv), sep=";").dropna(axis=1, how="all")
    return df

def get_best_times(df : pd.DataFrame) -> int:
    """Gets the winning time on the course"""
    times = df["Time"]
    times_in_seconds = times.transform(lambda t: int(t.split(":")[0])*60 + int(t.split(":")[1]))
    winning_time = min(times_in_seconds)
    return winning_time

def get_distance(df : pd.DataFrame) -> float:
    """Gets the distance of the course"""
    km = sum(df["km"]) or None
    return km
    
# to be a method of UserResult
def compile_event_details(obj : UserResult) -> None :
    """Populates the attributes of the UserResult object"""

    name = obj.name.replace(" ", "+")
    url = f"https://www.orienteering.ie/result2/?oaction=viewResults&league=&club=&map={obj.search_term}&SMonth=&SYear=&FMonth=&FYear=&comptr={name}&start=0&XXX=Search"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = get(url, headers=headers)
    table = r.text.split("tbody>")[1]

    id_list = table.split("moreResult&")[1:]
    obj.eventID = [ id_str.split('"')[0][3:] for id_str in id_list ]
    rows = table.split("<tr>")[1:]
    for entry in rows:
        print(entry)
        if "<td>" in entry:
            result_info = entry.split("<td>")
            course, date, month = result_info[-2][:-5], result_info[1][:-5], result_info[2][:-5]
            time = result_info[-1].replace(" ", "").split("</td>")[0]
            if "DNF" in time:
                time = None
            else:
                time = int(time.split(":")[0])*60 + int(time.split(":")[1])
            obj.course.append(course)
            obj.times.append(time)
            date = datetime.strptime(f"{date} {month}", "%d %b")
            obj.dates.append(date)
            



person = "Liam Cotter"
search = "Fota%"
obj = UserResult(person, search)
compile_event_details(obj)
print(obj.eventID)
print(obj.course)
index = 1
# for loop
df = get_df(obj.eventID[index])
relevant_data = df[df["Course"] == obj.course[index]]
winning_time = get_best_times(relevant_data)
distance = get_distance(relevant_data)
res = EventResult(obj.eventID[index], obj.course[index], obj.times[index], winning_time, distance, obj.dates[index])
res.set_calculations()
print(res)