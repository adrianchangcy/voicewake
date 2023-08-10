from django.apps import AppConfig
from django.conf import settings

class VoicewakeConfig(AppConfig):
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'voicewake'

    #override Django's ready()
    def ready(self):

        #import here, else error if imported outside
        from django.contrib.auth.models import Group
        from django.db.models.signals import post_save
            #signals sent by model system

        def handle_new_registered_users(sender, **kwargs):

            #expects User
            def add_to_default_group(user):

                group = Group.objects.get(name='regular')

                #expects User instance
                group.user_set.add(user)

            #run nested functions
            if kwargs['created']:

                #passes User instance
                add_to_default_group(kwargs['instance'])
            
            return

        #everytime AUTH_USER_MODEL is saved, call the function
        post_save.connect(
            handle_new_registered_users,
            sender=settings.AUTH_USER_MODEL
        )
        #looks like post_save.connect() will auto-send additional kwargs for us, which consists of:
            #['signal'], singal object
            #['instance'], user object
            #['created'], bool creation succcess
            #['updated_fields'], ??
            #['raw'], bool, ??
            #['using'], 'default', ??