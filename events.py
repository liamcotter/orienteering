import pandas as pd
from io import StringIO
from requests import get


class EventResult:
    def __init__(self, event_ID: int, course: str, time: int, date: str):
        """
        Initialises the EventResult object
        
        Parameters:
            event_ID (int): The ID of the event
            course (str): The course the user ran
            time (int): The time the user ran the course in seconds
            date (str): The date the event took place on
            winning_time (int): The winning time on the course in seconds
            distance (float): The distance of the course
            pace (float): The pace of the user in seconds per KM
            percent_behind (float): The percent behind the winner by time
        
        Examples:
            >>> EventResult(12345, "Course 1", 1807, "2020-01-01")

        """

        self.eventID = event_ID
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
            self.pace = self.time / self.distance  # assume seconds per KM
        self.percent_behind = 100 * ((self.time / self.winning_time) - 1)

    def add_event_data(self) -> None:
        """Adds the winning time and distance to the EventResult object"""
        df = get_df(self.eventID)
        course_data = df[df["Course"] == self.course]
        self.winning_time = get_best_time(course_data)
        self.distance = get_distance(course_data)
        self.set_calculations()


def get_df(eventID: int) -> pd.DataFrame:
    """
    Fetches the results CSV

    Parameters:
        eventID (int): The ID of the event

    Returns:
        pd.DataFrame: A dataframe of the event's results

    Examples:
        >>> get_df(12345)
           Course    Name       Time ...
        0    A    Tim Buktu     1807 ...
        1    B    Jim Donald    2234 ...
        2    B    Sven Carlson  3401 ...
        3    C    Robert Twist  3590 ...
        4    A    Bernie Cork   5523 ...

    """

    url = f"https://www.orienteering.ie/results/files/{str(eventID)[:-2]}/{str(eventID)}.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = get(url, headers=headers)
    except Exception as e:
        raise Exception("Request Error", e)
    if r.status_code != 200:
        raise Exception("Request Error: status code ", r.status_code)

    fixed_csv = r.text.replace(
        "(may be more) ...", "(may be more) ...;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;")
    if "<title>" in fixed_csv:
        raise Exception("No Results Found")
    df = pd.read_csv(StringIO(fixed_csv), sep=";").dropna(axis=1, how="all")
    return df


def get_best_time(df: pd.DataFrame) -> int:
    """
    Gets the winning time on the course

    Parameters:
        df (pd.DataFrame): The dataframe for the course

    Returns:
        int: The winning time on the course in seconds

    Examples:
        >>> get_best_time(df)
        1807

    """
    times = df["Time"].dropna()
    times_in_seconds = times.transform(lambda t: int(
        t.split(":")[0]) * 60 + int(t.split(":")[1]))
    winning_time = min(list(filterDNF(times_in_seconds)))
    return winning_time


def filterDNF(s: pd.Series):  # Generator
    """Filters out DNFs"""
    it = ((index, value) for index, value in s.items())
    _, prev = next(it)
    yield prev                      # Yield the first one
    for _, x in it:
        if prev <= x:
            yield x                 # Yield the ones that satisfy
            prev = x


def get_distance(df: pd.DataFrame) -> float:
    """
    Gets the distance of the course

    Parameters:
        df (pd.DataFrame): The dataframe for the course

    Returns:
        float: The distance of the course

    Examples:
        >>> get_distance(df)
        5.0

    """
    km = None
    if len(df["km"]) > 0:
        if float(df["km"].iloc[0]) == 0:
            km = None
        else:
            km = float(df["km"].iloc[0])
    return km
