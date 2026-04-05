
### django tests

#generate test data for test_metrics to test raw query performance
#coverage typically replaces .coverage
#if you want to run test cases separately and accumulate, use "--parallel-mode" then "combine" later
#for first arg, is load quantity, 1 is plenty just for sake of testing, >= 5 for performance test
#when you run coverage combine, it also performs erase
python manage.py shell -c "from voicewake.tests.test_metrics import RealisticBulkData; RealisticBulkData.sample_run(1, True, 2);"
#actual tests, using coverage (to skip coverage, replace "coverage run" with "python"):
    coverage erase;
    coverage run --parallel-mode manage.py test voicewake.tests.test_apis.Users_TestCase;
    coverage run --parallel-mode manage.py test voicewake.tests.test_apis.Core_TestCase;
    coverage run --parallel-mode manage.py test voicewake.tests.test_apis.Core_NormaliseAudioClips_TestCase;
    coverage run --parallel-mode manage.py test\
        voicewake.tests.test_metrics.BrowseEvents_TestCase.test_browse_events__apis__main_page\
        voicewake.tests.test_metrics.BrowseEvents_TestCase.test_browse_events__apis__own_page\
        voicewake.tests.test_metrics.BrowseEvents_TestCase.test_browse_events__apis__other_user_page\
        voicewake.tests.test_metrics.BrowseEvents_TestCase.test_browse_events__apis__own_like_dislike_page\
        --testrunner='voicewake.tests.test_metrics.TestRunnerWithMirror';
    coverage run --parallel-mode manage.py test voicewake.tests.test_cronjobs.Core_TestCase;
    coverage run --parallel-mode manage.py test voicewake.tests.test_cronjobs.Core_TransactionTestCase;
    coverage run --parallel-mode manage.py test voicewake.tests.test_services.HandleUserOTP_TestCase;
    coverage combine;
    coverage html;

#performance test
    #uses multiprocessing
    #run these test cases one by one to mitigate the impact of hardware as bottleneck
    #not worth running at CI/CD
    python manage.py test voicewake.tests.test_metrics.BrowseEvents_TestCase.test_browse_events__metrics__main_page\
        --testrunner='voicewake.tests.test_metrics.TestRunnerWithMirror';
    python manage.py test voicewake.tests.test_metrics.BrowseEvents_TestCase.test_browse_events__metrics__own_page\
        --testrunner='voicewake.tests.test_metrics.TestRunnerWithMirror';
    python manage.py test voicewake.tests.test_metrics.BrowseEvents_TestCase.test_browse_events__metrics__other_user_page\
        --testrunner='voicewake.tests.test_metrics.TestRunnerWithMirror';
    python manage.py test voicewake.tests.test_metrics.BrowseEvents_TestCase.test_browse_events__metrics__own_like_dislike_page\
        --testrunner='voicewake.tests.test_metrics.TestRunnerWithMirror';
    python manage.py test voicewake.tests.test_metrics.ListEventReplyChoices_TestCase.test_list_event_reply_choices\
        --testrunner='voicewake.tests.test_metrics.TestRunnerWithMirror';


#how to freeze packages for Django
    #in container:
        pip freeze > requirements.txt
    #at host machine:
        docker cp vw_dev-django_runserver-1:/requirements.txt .