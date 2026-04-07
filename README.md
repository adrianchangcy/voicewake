# voicewake.com
A queue-based audio social media website where two users can match and complete an event to be shown on the front page.

# 1. Introduction

## Why it was built
There is a market gap for offline audio interaction between strangers. We have WhatsApp, Facebook, Omegle, but there is no popular solution that mixes their strengths. This solution is not life-changing by any means. It was a way for me to upskill myself to bring an idea into reality. This solution has the ideal balance of being more complex than a To-Do app, while still allowing room for technical exploration through narrow scopes. Overall, it was a balance between project planning, system design, and learning new tools (Django, PostgreSQL, Docker, AWS, CI/CD, TypeScript, Vue, Tailwind, Redis, Celery, NGINX, CloudFront).

## Features
- passwordless login via time-based one-time password (TOTP) sent to email
- event creation by being the first to upload an audio clip
- time-based queue to match responders to reply and complete an event
- infinite content feed with filter selection for completed events, started/replied events, and liked/disliked audio clips
- audio normalisation
- content moderation via user reports, self-deletion, superuser deletion, and superuser bans
- cronjobs to handle expired replies and evaluate user reports

# 1. Local setup

## 1.1 Prerequisites

### Static LAN IP
- refer to the appropriate tutorial for your OS
- do this so the dev website can be visited on other LAN devices via dev device's static LAN IP
### SSL
- in stage and prod, if you have a service in front that terminates HTTPS to HTTP (e.g. AWS ALB) then you should modify NGINX and Vite to use HTTP, and skip steps for creating SSL
- in stage and prod, for direct HTTPS like NGINX <-> Cloudflare, continue with the steps
- in dev, refer to /nginx/readme on how to easily generate self-signed SSLs (suitable for dev only)
- do this for better environment consistency, even if self-signed SSL are not recognised in public
- in stage and prod, visit Cloudflare's page and create SSL files there
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
### .devcontainer (optional)
- within its own container, it installs all the VSCode plugins used, while downloading frontend and backend packages for linting and autocomplete
- you then make your VSCode reopen the project in container

### 1.2 Run Docker containers
    docker-compose --env-file ./env/.env --file ./docker-compose-dev.yaml up --build --no-deps --force-recreate -d
    docker-compose --env-file ./env/.env --file ./docker-compose-dev.yaml up django_runserver --build --no-deps --force-recreate -d

## 2. Deployment

### Option A (full cloud-native services)
- launch ECS using images from ECR (Gunicorn, Celery), then set up RDS (PostgreSQL), ElastiCache (Redis), and ALB
- have your URL resolve to ALB's public IP
- at security group's inbound/outbound rules, allow only traffic from ALB
- no need to manually create any SSL files
- this strictly follows security best practices for a production environment
- can be too expensive for a tiny project
- can be overkill for a project with 99% static files
<img src="https://github.com/user-attachments/assets/decd4446-b486-46d1-ac2e-63ca2ee58673" style="width: 100%; height: auto; display: block;">

### Option B (EC2 or VPS)
- refer to /ec2-setup-without-nat/ec2-setup.sh
- if you want to create repos for a system with 0 access to internet (a.k.a. air-gapped), refer to /ec2-setup-without-nat/ec2-create-offline-repo.sh
- create your repo in a live instance, since their public images are behind in versioning, and can cause complex installation errors later
- must manually create SSL files at Cloudflare's website, then paste into the machine for NGINX to use
<img src="https://github.com/user-attachments/assets/477d4ebb-27eb-45cc-bd85-cc092106799f" style="width: 100%; height: auto; display: block;">


# 3. Tests

## 3.1 Frontend (0 tests, 100% do not recommend)
- thought having a strongly tested backend is good enough
- felt fine when manually testing as components are being built
- unsustainable towards the final stages, since one small change requires entire steps of manual testing
- the early speed is only beneficial during "new components on bare pages"
- will slow down collaboration
- refer to Jest/Vitest for unit and component testing
- refer to Playwright/Cypress for UI-heavy flows via end-to-end testing

## 3.2 Backend
### 3.2.1 Separation of tests
#### Issue
- Django's default testing behaviour is to auto-create test db, then destroy it after the tests
- you can persist the test db, but it's only seamless enough for test-and-check steps
#### Solution
- create a custom TestRunner (TestRunnerWithMirror) with extra db specification at settings
- run db data mocking against live dev db, which will persist while not interfering with test db
- freely choose when to use the TestRunner at cmd via "--testrunner=..." for separation of integration and performance tests
### 3.2.2 Prepare persistent db data for TestRunnerWithMirror
    #this will generate around 150k audio_clip rows if the first arg is 1
    python manage.py shell -c "from voicewake.tests.test_metrics import RealisticBulkData; RealisticBulkData.sample_run(1, True, 2);"
### 3.2.3 90% test coverage for unit and integration tests
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
### 3.2.4 Sub-150ms query time for performance tests
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

# 2. Engineering insights (deep dive)

## 2.1 Frontend

### 2.1.1 Performant infinite scrolling

Challenges:
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

Challenges:
- redundant refetch of content via selection of previous filters
- on accidental navigation, scrolled progress and content is lost

Solutions:
- use Pinia to persist data and store scroll position
- use nested objects with filter selections as keys, e.g. my_data['filter0_choice']['filter1_choice'] = {}
- with manual page refresh or home page visit, clear Pinia data
- use TypeScript's interface for significantly better DX

Tradeoffs:
- still vulnerable to memory or localStorage overload if scrolling forever
- shelved the concern above due to high threshold (around 1kb per event) and reality of minimal content on live launch

### 2.1.3 Custom playback component

Challenges:
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
- fully addresses all challenges and requirements
- better code familiarity for faster troubleshooting
- significant time cost is unavoidable
- compounding code complexity when addressing HTML issues along with bugs from extra libraries used (Animejs)

## 2.2 Backend

### 2.2.1 Passwordless email TOTP login

Challenges:
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

Challenges:
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

### 2.2.3 Normalisation

Challenges:
- different users have different devices and input levels when recording
- the quiet parts can be too quiet, and the loud parts can be too loud
- for listening devices with EQ but no limiter, these spikes above 0dBFS can cause severe loud clipping (like popping a balloon)
- no straightforward way to mitigate surprises

Solutions:
- use FFMPEG within Lambda to directly normalise audio clips from S3 to balance the quietest and loudest parts
- use FFPMEG within Lambda to return audio volume peaks (loudest level for each chunk)
- follow EU's regulation for normalising to LUFS -23 via FFMPEG with args "loudnorm=I=-23:LRA=7:TP=-2"
- show the volume peaks at frontend

Tradeoffs:
- may cause noise to be more obvious, and may cause the loss of dynamic range
- luckily, for the context of this website, you do not need extreme quality to make words audible

### 2.2.4 Content moderation

Challenges:
- nature of user-generated content
- no moderators

Solutions:
- superuser can delete audio clips and ban users directly
- users can report other audio clips
- cronjob will evaluate reported audio clips

Tradeoffs:
- the cronjob has no room for nuanced judgment
- the cronjob can be manipulated
- the cronjob is currently the best compromise for a tiny userbase, but its evaluation rules will fall apart once there are a handful of active users







