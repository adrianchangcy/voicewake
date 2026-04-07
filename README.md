voicewake.com
A queue-based audio social media website where two users can match and complete an event to be shown on the front page.

# Table of Contents
Introduction
    Why it was built

Dev setup
    General
        .env
        Docker containers
        S3 for Django media
        Static LAN IP to your dev device
        NGINX SSL

Deployment
    Option 1: ALB+ECS+RDS+ElastiCache
    Option 2: EC2

Tests
    Frontend
        Why 0 tests
    Backend
        90% REST APIs coverage
        Sub-150ms complex queries

Core process flows
    Users
    New audio clips
    Event queues


System architecture
    Frontend
        Custom playback component
        Performant infinite scrolling
        Data management and persistence
    Backend
        Passwordless email TOTP login
        Raw queries for front page
        Audio clip features
        Cronjobs
        Content moderation
    Database
        3NF, b-tree indexes, composite indexes
    AWS
        Lambda, S3, CloudFront, SES
    CI/CD
        Github Actions
Lessons learned


# Introduction

### Why it was built
I wanted to upskill myself by bringing an idea into reality. It must be more complex than a To-Do app, while still allowing room for technical exploration through narrow scopes. Overall, it was a balance between learning new tools (Django, PostgreSQL, Docker, AWS, CI/CD, TypeScript, Vue, Tailwind, Redis, Celery, NGINX, CloudFront, .devcontainer), project planning, and system design.


# 2. System architecture (deep dive)

## 2.1 Frontend

### 2.1.1 Custom playback component

Issues:
- HTML audio playback animation isn't smooth
- HTML audio has unpleasant DX from async .play() and sync .pause()
- HTML audio's .seek to end causes 0.5s forced playback for it to become .ended=true
- public components are few, highly opinionated, buggy or unmaintained, or unrefined at small details

Additional requirements:
- must display audio volume peaks
- must integrate into infinite scrolling performantly
- must blend in with the website's design language

Solutions:
- use custom animation and couple it tightly with playback
- one-off play() and pause() for better DX
- display peaks via 1 HTML Canvas instead of 20 HTML divs
- stealthily allow HTML Audio to force-play itself at the end without users knowing
- use event listener to detect screen width changes so it can redraw and sync everything

Tradeoffs:
- fully addresses all issues and requirements
- better code familiarity for faster troubleshooting
- significant time cost is unavoidable
- compounding code complexity when addressing HTML issues along with bugs from extra libraries used (Animejs)

### 2.1.2 Performant infinite scrolling

Issues:
- high UI lag when combining scrolling and hundreds of HTML elements
- too many HTML elements to display

Solutions:
- use virtual scrolling (vue-virtual-scroller) to limit elements and manipulating their positions to simulate scrolling
- lightweight button representation for each audio clip
- replace every 20-div peaks with 1 HTML Canvas
- combine 1 VPlayback and Vue Teleport to replace selected audio clip's representation

Tradeoffs:
- minimal, since vue-virtual-scroller is well-developed
- some time cost required for learning HTML Canvas and its quirks

### 2.1.3 Data management for infinite content

Issues:
- redundant refetch of content via selection of previous filters
- on accidental navigation, scrolled progress and content is lost

Solutions:
- use Pinia to persist data and store scroll position
- use nested objects with filter selections as keys, e.g. my_data['filter0_choice']['filter1_choice'] = {}
- with manual page refresh or home page visit, clear Pinia data

Tradeoffs:
- still vulnerable to memory or localStorage overload if scrolling forever
- shelved the concern above due to high threshold and reality of minimal content on live launch


## 2.2 Backend

### 2.2.1 Passwordless email TOTP login

Issues:
- conventional passwords are hard to remember
- passkeys and multi-factor auth are overkill, given the website's casual risk-free context

Solutions:
- seamless frontend SPA interface for registration and sign-up
- reuse and redefine Django's auth to store passwordless new users
- generate random bytes as unique keys for each user for time-based one-time password (TOTP) generation
- generate TOTP on-demand to send to user's email
- mitigate brute-force attacks by tracking attempts in db

Tradeoffs:
- more mitigation steps required to prevent one user from using another user's email and locking them out from login
- involves enforcing attempt limits with reasonable cooldown, rate limiting
- HTML for email is notoriously difficult to work with
- requires third-party email service (AWS SES) to sign emails via DomainKeys Identified Mail (DKIM), so they don't end up in spam folder

### 2.2.2 Filter-based and cursor-based pagination

Issues:
- even with great db design (3NF, etc.), complex queries are unavoidable
- Django's Object Relational Mapper (ORM), meant for simplifying db queries, hits its limits (harder to read and maintain than raw queries)

Solutions:
- use logic at application layer to "build" raw queries to cater to different needs
- 3NF db design from the beginning, appropriate use of b-tree indexes and composite indexes
- careful evaluation of unnecessary row/table transaction locks at application layer
- debug indexes via the use of query planner (EXPLAIN ANALYZE)
- debug the overuse of subqueries using Django Debug Toolbar

Tradeoffs:
- complexity introduces onboarding challenges for future developers, on top of the fact that not everyone likes raw queries
- setting up mock data for thorough testing is complex (intentional absent data, predictable earliest/middle/latest positions of rows across an entire table, etc.)
- careful limitation of data during test case setup to mitigate O(n^2), since filter selection types create combinations
- complex test suite, must use nested for-loops to generate test cases, and implement test case index tracking
- added complexity of introducing true multithreading to scale CPU-bound test loads via "multiprocessing" package (not "theading")

### 2.2.3  Content moderation

Issues:
- nature of user-generated content
- no moderators

Solutions:
- superuser can delete audio clips and ban users directly
- users can report other audio clips
- cronjob will evaluate reported audio clips

Tradeoffs:
- no room for nuanced judgment
- easy to manipulate
- currently the best compromise for tiny userbase

## Database
To save costs and match the tiny userbase, I chose  host PSQL as a container in EC2 along with the other services. EC2 will have pgbackrest for automatic incremental backup to S3. I'm fully aware that databases are critical aspects that should be hosted on managed services like AWS RDS.

## AWS
To save development time and simplify project scopes, these AWS services (Lambda, S3, SES, CloudFront) are directly implemented for dev/stage/prod. This means that there are no "local machine" versions for file and email handling.

## CI/CD with Github Actions
- uses OIDC for AWS credentials as part of best security practice in preventing long-lived secrets
- on branch pull request to main, it will run tests, build Docker images and deploy to stage and prod ECR, do Vite bundling and upload to stage S3
- on success and merge, it will run tests, do Vite bundling and upload to prod S3







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
