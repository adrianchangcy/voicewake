
#time window in seconds for listener events to qualify for live
QUALIFY_FOR_LIVE_TIME_WINDOW = 60

#extra minutes for initial time during listener new event
LISTENER_NEW_EVENT_EXTRA_MINUTES = 2


LISTENER_EVENT_SEARCH_LIMIT = 3


#file extensions allowed
#aac is the ideal format, but not used
    #requires additional configurations
    #not supporting formats like flac saves us server resources (allow only for paid requests?)
AUDIO_FILE_EXTENSIONS_ALLOWED = ['mp3', 'webm']
HTML_FILE_INPUT_ACCEPT = '.mp3, .webm'

#max file size
#assumes decimal is always used (1000 ** 2) over binary (1024 ** 2)
MAX_AUDIO_FILE_SIZE_MB = 200