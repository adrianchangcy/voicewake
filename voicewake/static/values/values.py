#OLD:

#time window in seconds for listener events to qualify for live
QUALIFY_FOR_LIVE_TIME_WINDOW = 60

#extra minutes for initial time during listener new event
LISTENER_NEW_EVENT_EXTRA_MINUTES = 2

#max listener events to show to talker
LISTENER_EVENT_SEARCH_LIMIT = 3

#maximum wait time given to talker on selecting a listener event
TALKER_EVENT_CHOICE_MAX_DURATION_SECONDS = 10

#file extensions allowed
#aac is the ideal format, but not used
    #requires additional configurations
    #not supporting formats like flac saves us server resources (allow only for paid requests?)
AUDIO_FILE_EXTENSIONS_ALLOWED = ['mp3', 'webm']
HTML_FILE_INPUT_ACCEPT = '.mp3, .webm'

#max file size
#assumes decimal is always used (1000 ** 2) over binary (1024 ** 2)
MAX_AUDIO_FILE_SIZE_MB = 200



#NEW:

#uses checkpoint of today 00:00:00 and counts with when_created__gte=...
#for max _ event_room a user can create per day
MAX_DAILY_CREATED_EVENT_ROOMS = 5

#uses checkpoint of today 00:00:00 and counts with when_created__gte=...
#for max _ replies a user can create per day
MAX_DAILY_CREATED_REPLY_EVENTS = 5

#unlocks event_room if last when_locked is too long ago
#if user has page open, JS will ping to update when_locked
REPLY_INACTIVE_MAX_MINUTES = 30

REPLY_CHOICE_INACTIVE_MAX_MINUTES = 10

#how many incomplete EventRooms to show at a time, before next reroll
INCOMPLETE_EVENT_ROOMS_PER_ROLL = 1

#e.g. top 10 completed events, etc.
SPECIAL_EVENT_ROOMS_QUANTITY = 10


#for cronjob
CRONJOB_ROW_LIMIT = 50



