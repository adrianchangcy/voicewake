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
        from .models import AuthUser, UserDetails, EventRoles, UserEventRoles, Countries, Languages

        def handle_new_registered_users(sender, **kwargs):

            def create_user_details(user):

                #should get user's geolocation instead of these
                DEFAULT_COUNTRY = Countries.objects.get(
                    country_name='United States of America',
                    country_name_shortened='USA'
                )
                DEFAULT_LANGUAGE = Languages.objects.get(
                    language_name='English',
                    language_name_shortened='ENG'
                )

                #check if user_id exists instead of direct get_or_create()
                #only want one row for one user
                try:

                    user_detail = UserDetails.objects.get(user=getattr(user, 'id'))

                except UserDetails.DoesNotExist:

                    user_detail = UserDetails.objects.create(
                        user=AuthUser(pk=getattr(user, 'id')),
                        country=DEFAULT_COUNTRY,
                        language=DEFAULT_LANGUAGE,
                        user_display_name=getattr(user, 'username'),  #user can change again later
                        user_birthdate='2022-01-01',
                    )

            def add_to_default_group(user):

                group = Group.objects.get(name='regular')
                group.user_set.add(user)

            def add_with_event_roles(user):

                event_role = EventRoles.objects.get(event_role_name='originator')

                user_event_role, ok = UserEventRoles.objects.get_or_create(
                    user=AuthUser(pk=getattr(user, 'id')),
                    event_role=EventRoles(pk=getattr(event_role, 'id')),
                    defaults={},
                )

                event_role = EventRoles.objects.get(event_role_name='responder')

                user_event_role, ok = UserEventRoles.objects.get_or_create(
                    user=AuthUser(pk=getattr(user, 'id')),
                    event_role=EventRoles(pk=getattr(event_role, 'id')),
                    defaults={},
                )

            #run nested functions
            if kwargs['created']:

                user = kwargs['instance']

                create_user_details(user=user)
                add_to_default_group(user=user)
                add_with_event_roles(user=user)
            
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