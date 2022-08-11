#here, we define business logic

#Python libraries
from datetime import datetime, timezone, timedelta
import zoneinfo

#app files
from .models import *
from .serializers import *




def store_talker_audio_file(user, event, file):

    pass