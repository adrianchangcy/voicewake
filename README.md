# voicewake.com
A queue-based audio social media website where two users can match and complete an event to be shown on the front page.

order (uppercases):
1motivation
2features
3architecture (put all charts and diagrams here, including CI/CD)
3system infrastructure (cloud setup)
3data model (abstracted ERD)
3system logic (sequence/flow)
4engineering insights (challenges & solutions)
4tool evaluation
5local setup
6tests
7deployment
8future improvements (feature + (why not done))
7credits
7licenses




# 1. Motivation

There is a market gap for offline audio interaction between strangers. We have WhatsApp, Facebook, Omegle, but there is no popular solution that mixes their strengths.

By no means am I expecting this website to be life-changing for anybody. It's primarily a way for me to upskill myself by bringing an idea into reality. It is more complex than a To-Do app, while still allowing room for technical exploration.

Overall, it was a balance between project planning, system design, and learning new tools (Django, PostgreSQL, Docker, AWS, CI/CD, TypeScript, Vue, Tailwind, Redis, Celery, NGINX, CloudFront).



# 2. Features
- passwordless login via time-based one-time password (TOTP) sent to email
- event creation by being the first to upload an audio clip
- time-based queue to match responders to reply and complete an event
- infinite content feed with filter selection for completed events, started/replied events, and liked/disliked audio clips
- audio normalisation
- content moderation via user reports, self-deletion, superuser deletion, and superuser bans
- cronjobs to handle expired replies and evaluate user reports



# 3. Architecture

## 3.1 System Infrastructure

### Option A: Fully Cloud-Native Services
<img src="https://github.com/user-attachments/assets/decd4446-b486-46d1-ac2e-63ca2ee58673" style="width: 100%; height: auto; display: block;">

### Option B: EC2 or VPS with Minor Cloud Services
<img src="https://github.com/user-attachments/assets/477d4ebb-27eb-45cc-bd85-cc092106799f" style="width: 100%; height: auto; display: block;">

## 3.2 Data Model (Abstracted ERD)
<img src="https://github.com/user-attachments/assets/ec295dbc-6fda-45de-a895-5db2e815f4b2" style="width: 100%; height: auto; display: block;">

## 3.3 System Logic (Sequence/Flow)

### Login
<img src="https://github.com/user-attachments/assets/a182c63d-7b69-494e-be02-47498d1035cf" style="width: 100%; height: auto; display: block;">

### Create Event
<img src="https://github.com/user-attachments/assets/21abdfb6-faef-4ca3-be02-b357c83e39f8" style="width: 100%; height: auto; display: block;">

### Reply
<img src="https://github.com/user-attachments/assets/e42ab4d3-6a41-4db8-a5b2-ae1e7c22afd6" style="width: 100%; height: auto; display: block;">



# 4. Engineering Insights (Challenges & Solutions)

## 4.1 Frontend

### 4.1.1 Performant Infinite Scrolling

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

### 4.1.2 Data Management for Infinite Content

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

### 4.1.3 Custom Playback Component

Challenges:
- HTML audio playback animation isn't smooth
- HTML audio has unpleasant DX from async .play() and sync .pause()
- HTML audio's .seek to end causes 0.5s forced playback for it to become .ended=true
- public components are few, highly opinionated, buggy or unmaintained, or unrefined at small details
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

### 4.1.4 Countdown with Worker()

Challenges:
- when the user switches browser tabs, the main thread for the website is paused, affecting setInterval()
- this causes recording duration to pause, preventing appropriate limiting
- this causes reply and confirmation durations to pause, preventing appropriate limiting

Solutions:
- create a Web Worker file that the browser's Worker() can use to continue the countdown in its own background thread
- another problem pops up, where Worker() has strict CORS policy, meaning directly loading a Web Worker file from CloudFront is denied
- after troubleshooting, it is due to CloudFront requiring specific request headers to be present
- you cannot force headers into Worker()'s requests
- to solve this, use a frontend patcher that uses "code literal" technique, which also loads the CloudFront file into a Blob object
- this has an added benefit of maintaining frontend/backend separation, by not requiring special CORS treatment at the backend

Tradeoffs:
- higher time cost and complexity, due to how challenging it was to figure out and implement a solution
- you also need to run Vite build with custom flags declared at vite.config.ts, for it to insert the correct Web Worker source during bundling
- this complexity ensures that local dev can serve local Web Worker, while stage and prod will deploy the Web Worker file normally to S3 along with other files
- this complexity remains isolated to the frontend and Vite, allowing for no special attention in other areas (backend/AWS/etc.)
- NGINX will match "/static/..." directory requests to CloudFront

## 4.2 Backend

### 4.2.1 Passwordless Email TOTP Login

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

### 4.2.2 Filter-Based and Cursor-Based Pagination

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

### 4.2.3 Normalisation

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

### 4.2.4 Content Moderation

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

## 4.3 Tool Evaluation







# 5. Local Setup

## 5.1 Prerequisites

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
- to save dev time, workflow_dispatch was not used, which would otherwise allow for explicit control of steps (e.g. only deploy frontend if only updating frontend, etc.)
### .env
- refer to /.env/example.env
- fill it in with the secrets you've gathered
### Logging
- due to simple deployment, currently just telling Django to write into error.log
### .devcontainer (optional)
- within its own container, it installs all the VSCode plugins used, while downloading frontend and backend packages for linting and autocomplete
- you then make your VSCode reopen the project in container

### 5.2 Run Docker containers
    docker-compose --env-file ./env/.env --file ./docker-compose-dev.yaml up --build --no-deps --force-recreate -d
    docker-compose --env-file ./env/.env --file ./docker-compose-dev.yaml up django_runserver --build --no-deps --force-recreate -d



# 6. Tests

## 6.1 Frontend
- 0 tests (100% do not recommend)
- my mistake was from judging how easy it was to manually test when creating new components on blank pages
- this was nearly unsustainable towards the final stages, with one small change requiring entire steps of manual tests
- automated tests must be created before any future development and collaboration
- refer to Jest/Vitest for unit and component testing
- refer to Playwright/Cypress for UI-heavy flows via end-to-end testing

## 6.2 Backend
### Database Separation for Different Tests
#### Issue
- Django's default testing behaviour is to auto-create test db, then destroy it after the tests
- you can persist the test db, but it's only seamless enough for test-and-check steps
#### Solution
- create a custom TestRunner (TestRunnerWithMirror) with extra db specification at settings
- run db data mocking against live dev db, which will persist while not interfering with test db
- freely choose when to use the TestRunner at cmd via "--testrunner=..." for separation of integration and performance tests

### 6.2.1 Prepare persistent db data for TestRunnerWithMirror
    #this will generate around 150k audio_clip rows if the first arg is 1
    python manage.py shell -c "from voicewake.tests.test_metrics import RealisticBulkData; RealisticBulkData.sample_run(1, True, 2);"
    
### 6.2.2 90% test coverage for unit and integration tests
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

### 6.2.3 Sub-150ms query time for performance tests
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



# 7. Deployment

## Option A: Fully Cloud-Native Services
- launch ECS using images from ECR (Gunicorn, Celery), then set up RDS (PostgreSQL), ElastiCache (Redis), and ALB
- have your URL resolve to ALB's public IP
- at security group's inbound/outbound rules, allow only traffic from ALB
- no need to manually create any SSL files
- this strictly follows security best practices for a production environment
- can be too expensive for a tiny project
- can be overkill for a project with 99% static files

## Option B: EC2 or VPS with Minor Cloud Services
- refer to /ec2-setup-without-nat/ec2-setup.sh
- if you want to create repos for a system with 0 access to internet (a.k.a. air-gapped), refer to /ec2-setup-without-nat/ec2-create-offline-repo.sh
- create your repo in a live instance, since their public images are behind in versioning, and can cause complex installation errors later
- must manually create SSL files at Cloudflare's website, then paste into the machine for NGINX to use



# 8. Future Improvements



# 9. Credits



# 10. License








