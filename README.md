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


# 1. Prerequisites

## 1.1 Local

### Static LAN IP
- refer to the appropriate tutorial for your OS
- do this so the dev website can be visited on other LAN devices via dev device's static LAN IP
### SSL
- in prod, if you use private network NGINX <-> AWS ALB, then skip SSL, and modify /nginx/default.conf.template and /frontend/vite.config.js to use HTTP
- in prod, if you use public network NGINX <-> Cloudflare, continue with the steps
- refer to /nginx/readme on how to easily generate self-signed SSLs (suitable for dev only)
- do this for better environment consistency, even if self-signed SSL are not recognised in public
### AWS
- SES so your emails don't end up as spam
- S3 with 4 buckets: A for crucial files, B for static files, C for media files, and D for unprocessed files
- CloudFront to serve files from S3
- download FFMPEG and compress it into .zip, then upload to bucket A for Lambda to fetch later
- create Lambda that contains code from /voicewake/lambdas.py
### CI/CD
- set up your secrets at Github > repo > settings > environments
### .env
- refer to /.env/example.env
- fill it in with the secrets you've gathered

## 1.2 Stage/Prod
### SSL
- if you're doing private network NGINX <-> AWS ALB, skip this step
- if you're doing public network NGINX <-> Cloudflare, obtain SSL from Cloudflare, then use /.env/.env and /ec2-setup-without-nat/ec2-setup.sh as reference for NGINX to discover your SSL files

# 2. Setup

## 2.1 Local
### Build and run containers
    docker-compose --env-file ./env/.env --file ./docker-compose-dev.yaml up --build --no-deps --force-recreate -d
    docker-compose --env-file ./env/.env --file ./docker-compose-dev.yaml up django_runserver --build --no-deps --force-recreate -d
### .devcontainer (optional)
- within its own container, it installs all the VSCode plugins used, while downloading frontend and backend packages for linting and autocomplete
- you then make your VSCode reopen the project in container

## 2.2 Stage/Prod
### option A (full cloud-native services)
- make ECS get images from ECR (Gunicorn, Celery), then set up RDS (PostgreSQL), ElastiCache (Redis), and ALB
- have your URL resolve to ALB's public IP
- at security group's inbound/outbound rules, allow only traffic from ALB
- this is 100% the best way to go if you can afford it
### option B (EC2 or VPS)
- refer to /ec2-setup-without-nat/ec2-setup.sh

# 3. Tests

## 3.1 Frontend (0 tests, 100% do not recommend)
- thought having a strongly tested backend is good enough
- felt fine when manually testing as components are being built
- unsustainable towards the final stages, since one small change requires entire steps of manual testing
- the early speed is only benificial during "new components on bare pages"
- will slow down collaboration
- refer to Jest/Vitest for unit and component testing
- refer to Playwright/Cypress for UI-heavy flows via end-to-end testing

## 3.2 Backend
### 3.2.1 Prepare persistent db data for TestRunnerWithMirror
    #This will generate around 150k audio_clip rows if the first arg is 1
    python manage.py shell -c "from voicewake.tests.test_metrics import RealisticBulkData; RealisticBulkData.sample_run(1, True, 2);"
### 3.2.2 90% test coverage for unit and integration tests
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
### 3.2.2 Sub-150ms query time for performance tests
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

# 2. System architecture (deep dive)

## 2.1 Frontend

### 2.1.1 Performant infinite scrolling

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

### 2.1.2 Data management for infinite content

Issues:
- redundant refetch of content via selection of previous filters
- on accidental navigation, scrolled progress and content is lost

Solutions:
- use Pinia to persist data and store scroll position
- use nested objects with filter selections as keys, e.g. my_data['filter0_choice']['filter1_choice'] = {}
- with manual page refresh or home page visit, clear Pinia data
- use TypeScript's interface for significantly better DX

Tradeoffs:
- still vulnerable to memory or localStorage overload if scrolling forever
- shelved the concern above due to high threshold and reality of minimal content on live launch

### 2.1.3 Custom playback component

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







