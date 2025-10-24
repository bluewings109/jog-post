from datetime import datetime


class ActivityDomain:
    def __init__(
        self,
        activity_id: int,
        athlete_id: int,
        name: str,
        distance: float,
        elapsed_time: float,
        type: str,
        start_date: datetime,
        average_heartrate: float,
        max_heartrate: float,
        polyline: str,
        summary_polyline: str,
        post_date: datetime|None=None,
        is_posted: bool|None=None,
    ):
        self.activity_id=activity_id
        self.athlete_id=athlete_id
        self.name=name
        self.distance=distance
        self.elapsed_time=elapsed_time
        self.type=type
        self.start_date=start_date
        self.average_heartrate=average_heartrate
        self.max_heartrate=max_heartrate
        self.polyline=polyline
        self.summary_polyline=summary_polyline
        self.post_date=post_date
        self.is_posted=is_posted
