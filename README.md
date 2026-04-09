# voicewake.com
A queue-based audio social media website where two users can match and complete an event to be shown on the front page.


# Motivation

There is a market gap for audio interaction between strangers without live pressures. We have WhatsApp, Facebook, Omegle, but there is no popular solution that mixes their strengths.

By no means am I expecting this website to be the next Facebook. It's simply a way for me to upskill myself by bringing an idea into reality. It is more complex than a To-Do app, while still allowing room for technical exploration.

Overall, it was a balance between project planning, system design, and learning new tools (Django, PostgreSQL, Docker, AWS, CI/CD, TypeScript, Vue, Tailwind, Redis, Celery, NGINX, CloudFront).



# Features
- passwordless login via time-based one-time password (TOTP) sent to email
- event creation by being the first to upload an audio clip
- time-based queue to match responders to reply and complete an event
- infinite content feed with filter selection for completed events, started/replied events, and liked/disliked audio clips
- audio normalisation
- content moderation via user reports, self-deletion, superuser deletion, and superuser bans
- cronjobs to handle expired replies and evaluate user reports



# Table of Contents
- [1. Architecture](#1-architecture)
  - [1.1 System Infrastructure](#11-system-infrastructure)
    - [Option A: Fully Cloud-Native Services](#option-a-fully-cloud-native-services)
    - [Option B: EC2 or VPS with Minor Cloud Services](#option-b-ec2-or-vps-with-minor-cloud-services)
  - [1.2 Data Model (Abstracted ERD)](#12-data-model-abstracted-erd)
  - [1.3 System Logic (Sequence/Flow)](#13-system-logic-sequenceflow)
    - [Login](#login)
    - [Create Event](#create-event)
    - [Reply](#reply)
- [2. Engineering Insights (Challenges \& Solutions)](#2-engineering-insights-challenges--solutions)
  - [2.1 Frontend](#21-frontend)
    - [2.1.1 Performant infinite scrolling](#211-performant-infinite-scrolling)
    - [2.1.2 Data management for infinite content](#212-data-management-for-infinite-content)
    - [2.1.3 Custom playback component](#213-custom-playback-component)
    - [2.1.4 Countdown with worker()](#214-countdown-with-worker)
  - [2.2 Backend](#22-backend)
    - [2.2.1 Passwordless email TOTP login](#221-passwordless-email-totp-login)
    - [2.2.2 Filter-based and cursor-based pagination](#222-filter-based-and-cursor-based-pagination)
    - [2.2.3 Normalisation](#223-normalisation)
    - [2.2.4 Content moderation](#224-content-moderation)
    - [2.2.5 Likes and dislikes](#225-likes-and-dislikes)
  - [2.3 Tools Evaluation](#23-tools-evaluation)
- [3. Local Setup](#3-local-setup)
  - [3.1 Prerequisites](#31-prerequisites)
    - [Static LAN IP](#static-lan-ip)
    - [SSL](#ssl)
    - [AWS](#aws)
    - [CI/CD](#cicd)
    - [.env](#env)
    - [Logging](#logging)
    - [.devcontainer (optional)](#devcontainer-optional)
  - [3.2 Run Docker containers](#32-run-docker-containers)
- [4. Tests](#4-tests)
  - [4.1 Frontend](#41-frontend)
    - [0 tests (100% do not recommend)](#0-tests-100-do-not-recommend)
  - [4.2 Backend](#42-backend)
    - [Database Separation for Different Tests](#database-separation-for-different-tests)
    - [4.2.1 Prepare persistent db data for TestRunnerWithMirror](#421-prepare-persistent-db-data-for-testrunnerwithmirror)
    - [4.2.2 90% test coverage for unit and integration tests](#422-90-test-coverage-for-unit-and-integration-tests)
    - [4.2.3 Sub-150ms query time for performance tests](#423-sub-150ms-query-time-for-performance-tests)
- [5. Deployment](#5-deployment)
  - [Option A: Full Cloud-Native Services](#option-a-fully-cloud-native-services-1)
  - [Option B: EC2 or VPS with Minor Cloud Services](#option-b-ec2-or-vps-with-minor-cloud-services-1)
- [6. Future Improvements](#6-future-improvements)
- [7. Credits](#7-credits)
- [8. License](#8-license)
- [9. Contributions \& Forking](#9-contributions--forking)



# 1. Architecture

## 1.1 System Infrastructure

### Option A: Fully Cloud-Native Services
<img src="https://github.com/user-attachments/assets/decd4446-b486-46d1-ac2e-63ca2ee58673" style="width: 400; height: auto; display: block;">

### Option B: EC2 or VPS with Minor Cloud Services
<img src="https://github.com/user-attachments/assets/477d4ebb-27eb-45cc-bd85-cc092106799f" style="width: 400; height: auto; display: block;">

## 1.2 Data Model (Abstracted ERD)
<img src="https://github.com/user-attachments/assets/ec295dbc-6fda-45de-a895-5db2e815f4b2" style="width: 400; height: auto; display: block;">

## 1.3 System Logic (Sequence/Flow)

### Login
<img src="https://github.com/user-attachments/assets/a182c63d-7b69-494e-be02-47498d1035cf" style="width: 400; height: auto; display: block;">

### Create Event
<img src="https://github.com/user-attachments/assets/21abdfb6-faef-4ca3-be02-b357c83e39f8" style="width: 400; height: auto; display: block;">

### Reply
<img src="https://github.com/user-attachments/assets/e42ab4d3-6a41-4db8-a5b2-ae1e7c22afd6" style="width: 400; height: auto; display: block;">



# 2. Engineering Insights (Challenges & Solutions)

## 2.1 Frontend

### 2.1.1 Performant infinite scrolling

<details>
  <summary>View details</summary>

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

</details>

### 2.1.2 Data management for infinite content

<details>
  <summary>View details</summary>

Challenges:
- redundant refetch of content via selection of previous filters
- on accidental navigation, scrolled progress and content is lost

Solutions:
- use Pinia to persist data and store scroll position
- use nested objects with filter selections as keys, e.g. my_data['filter0_choice']['filter1_choice'] = {}
- with manual page refresh or home page visit, clear Pinia data
- use TypeScript's interface for significantly better DX

```typescript
            updateLastSelectedAudioClip(audio_clip:AudioClipsTypes|AudioClipsAndLikeDetailsTypes|null) : void {

                this.filtered_events_structure[
                    this.current_like_dislike_choice_index
                ][
                    this.current_event_generic_status_name_index
                ][
                    this.current_main_filter_index
                ][
                    this.current_timeframe_index
                ][
                    this.current_audio_clip_role_name_index
                ][
                    this.current_audio_clip_tone_id
                ][
                    'last_selected_audio_clip'
                ] = audio_clip;
            },
```

Tradeoffs:
- theoretically still vulnerable to memory or localStorage overload if scrolling forever
- shelved the concern due to high threshold (around 1kb per event) and reality of minimal content on live launch

</details>

### 2.1.3 Custom playback component

<details>
  <summary>View details</summary>
  
Challenges:
- HTML audio playback animation isn't smooth
- HTML audio has unpleasant DX from async .play() and sync .pause()
- HTML audio's .seek to end causes 0.5s forced playback for it to become .ended=true
- public components are few, highly opinionated, buggy or unmaintained, or unrefined at small details
- must display audio volume peaks
- must integrate into infinite scrolling performantly
- must blend in with the website's design language

<video src="https://github.com/user-attachments/assets/7ac5b80c-cffb-4ee3-b57b-20fb31078f07" width="100%" style="object-fit: contain;" controls muted>
  Your browser does not support the video tag.
</video>

Solutions:
- use custom animation and couple it tightly with playback
- one-off play() and pause() for better DX
- display peaks via 1 HTML Canvas instead of 20 HTML divs
- stealthily allow HTML Audio to force-play itself at the end without users knowing
- use event listener to detect screen width changes so it can redraw and sync everything

<video src="https://github.com/user-attachments/assets/c5a94fdf-659e-4f14-908c-0fe6250b6b35" width="100%" style="object-fit: contain;" controls>
  Your browser does not support the video tag.
</video>

Tradeoffs:
- fully addresses all challenges and requirements
- better code familiarity for faster troubleshooting
- significant time cost is unavoidable
- compounding code complexity when addressing HTML issues along with bugs from extra libraries used (Animejs)

</details>

### 2.1.4 Countdown with worker()

<details>
  <summary>View details</summary>

Challenges:
- when the user switches browser tabs, the main thread for the website is paused, affecting setInterval()
- this causes recording duration to pause, preventing appropriate limiting
- this causes reply and confirmation durations to pause, preventing appropriate limiting

Solutions:
- create a Web Worker file that the browser's Worker() can use to continue the countdown in its own background thread
- upload bundled Web Worker file to S3 for stage and prod

Secondary Challenges:
- stage and prod Web Worker URL issue pops up
- CloudFront expects certain headers in requests to send data
- you cannot force headers into Worker()'s requests
- CloudFront returns access denied

Secondary Solutions:
- use a frontend patcher to redefine Worker(), which will now use "code literal" technique, which also loads the CloudFront file into a Blob object
- this has an added benefit of maintaining frontend/backend separation, by not requiring special CORS treatment at the backend

```typescript
typeof window !== "undefined" &&
    (Worker = ((BaseWorker: typeof Worker) =>
        class Worker extends BaseWorker {
            constructor(scriptURL: string | URL, options?: WorkerOptions) {
                const url = String(scriptURL);
                super(
                    // Check if the URL is remote
                    url.includes("://") && !url.startsWith(location.origin)
                    ? // Launch the worker with an inline script that will use `importScripts`
                    // to bootstrap the actual script to work around the same origin policy.
                    URL.createObjectURL(
                        new Blob(
                            [
                                // Replace the `importScripts` function with
                                // a patched version that will resolve relative URLs
                                // to the remote script URL.
                                //
                                // Without a patched `importScripts` Webpack 5 generated worker chunks will fail with the following error:
                                //
                                // Uncaught (in promise) DOMException: Failed to execute 'importScripts' on 'WorkerGlobalScope':
                                // The script at 'http://some.domain/worker.1e0e1e0e.js' failed to load.
                                //
                                // For minification, the inlined variable names are single letters:
                                // i = original importScripts
                                // a = arguments
                                // u = URL
                                `importScripts=((i)=>(...a)=>i(...a.map((u)=>''+new URL(u,"${url}"))))(importScripts);importScripts("${url}")`,
                            ],
                            { type: "text/javascript" }
                        )
                    )
                    : scriptURL,
                    options
                );
            }
        })(Worker)
    );
```

Tradeoffs:
- higher time cost and complexity, due to how challenging it was to figure out and implement a solution
- you also need to run Vite build with custom flags declared at vite.config.ts, for it to insert the correct Web Worker source during bundling
- this complexity ensures that local dev can serve local Web Worker, while stage and prod will deploy the Web Worker file normally to S3 along with other files
- this complexity remains isolated to the frontend and Vite, allowing for no special attention in other areas (backend/AWS/etc.)
- NGINX will match "/static/..." directory requests to CloudFront

</details>

## 2.2 Backend

### 2.2.1 Passwordless email TOTP login

<details>
  <summary>View details</summary>

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

</details>

### 2.2.2 Filter-based and cursor-based pagination

<details>
  <summary>View details</summary>

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

</details>

### 2.2.3 Normalisation

<details>
  <summary>View details</summary>

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

</details>

### 2.2.4 Content moderation

<details>
  <summary>View details</summary>

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

</details>

### 2.2.5 Likes and dislikes

<details>
  <summary>View details</summary>

Challenges:
- one user can easily have hundreds of likes in the future
- potentially one of the earliest points of the system to hit scaling limits
- heavy and frequent read/write, especially for populating test database
- highly susceptible to race conditions

Solutions:
- at frontend, allow users to spam actions, but implement a delay that resets on every action, to ideally only send the "last" action to server
- at backend (important), group the update of likes/dislikes table and metrics table within the same atomic transaction, and use row-level lock for metrics table
- at database, ensure heavy-write metrics table is separated from heavy-read audio clips table, so row locks on metrics don't affect other updates on audio clips
- at database, avoid the use of triggers, so row insertions for populating test database remain frictionless

Tradeoffs:
- fairly complex concepts to grasp in practice
- difficult to write tests for race conditions, so implementing solutions must require adequate understanding in advance

</details>

## 2.3 Tools Evaluation
<table>
  <tr>
    <th>Tool</th>
    <th>Pros</th>
    <th>Cons</th>
    <th>Alternative Tool</th>
    <th>Pros</th>
    <th>Cons</th>
    <th>Justification</th>
  </tr>
  <tr>
    <td>Django</td>
    <td>batteries-included, well-maintained, excellent documentation, built on top of Python</td>
    <td>carries over Python's greatest strength (and weakness) of poor DX, autocomplete, and typing, when handling complex data such as dicts</td>
    <td>Golang</td>
    <td>prides itself on being easy to code, read, and maintain, superior performance, with static typing available</td>
    <td>lacking in packages for future complexities</td>
    <td>already well-versed with Python, much easier access to Python's immense variety of public packages to save on dev time, with no existing userbase to justify Golang's superior performance that can only be seen at scale</td>
  </tr>
  <tr>
    <td>Vue</td>
        <td>superior DX, easier for beginners and maintenance via Options API, clear separation of HTML and logic, more sensible on optimisation (e.g. default opt-out on rerenders vs. React's default opt-in), has excellent complementary Pinia for state management and persistence, generally more opinionated for superior consistency and easier onboarding across projects</td>
        <td>lack of high quality components for complex use cases</td>
    <td>React</td>
        <td>popularity contributes to wider variety of higher quality packages, superior usability, easier to find collaborators</td>
        <td>too tightly coupled between HTML and logic, too much freedom in how a project can be designed</td>
    <td>Vue is more sensible with better DX, but may be less feasible from collaboration and hiring perspective</td>
  </tr>
  
  <tr>
      <td>PostgreSQL</td>
          <td>mature ACID compliance, mature and battle-tested, first-class support from Django, well-maintained, actively developed, readily supports more column types like arrays (for audio volume peaks)</td>
          <td>lack of native specialty tools, but has high quality 3rd party tools readily available, e.g. Pgpool-II for reusing connections, load balancing SELECT queries, etc., and pgBackRest for automatic incremental backup and recovery that's safer than pg_dump</td>
      <td>MongoDB (NoSQL)</td>
          <td>easier to prototype with, better at scaling horizontally, highly flexible for loose data relations</td>
          <td>weakly enforced data relations will introduce complexity to systems and tests, not natively supported by Django</td>
      <td>already experienced with raw SQL queries, Django has first-class support for PostgreSQL, comes with all the benefits of a relational database, wide cloud support, battle-tested, with no current use case for handling complex loosely structured data to justify MongoDB</td>
  </tr>

  <tr>
      <td>Redis</td>
          <td>feature-rich, easy to use, simple, wide cloud support</td>
          <td>may have more cost and legal hurdles</td>
      <td>Valkey</td>
          <td>straightfoward open source licensing, is a direct drop-in replacement for Redis due to it being a fork of Redis</td>
          <td>higher chance of being less compatible across different tools</td>
      <td>Redis was the obvious (and dominant) choice when the project had started, well before its licensing backlash, and I wanted to maintain my focus on development at the time</td>
  </tr>

  <tr>
      <td>AWS</td>
          <td>more readily at serving US traffic (ideal target audience), incredible maturity, most dominant market share, offers more specialised services for complex needs, attractive free tier, easier to land a job upon decent mastering of it</td>
          <td>can be overkill for small projects compared to a VPS if strictly going full cloud-native</td>
      <td>GCP</td>
          <td>generally lower costs, superior Kubernetes support and maturity</td>
          <td>smaller market share, less mature</td>
      <td>since learning opportunities and job prospects were top priority, AWS was the clear winner with its free tier</td>
  </tr>
</table>



# 3. Local Setup

## 3.1 Prerequisites

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

## 3.2 Run Docker containers
    docker-compose --env-file ./env/.env --file ./docker-compose-dev.yaml up --build --no-deps --force-recreate -d
    docker-compose --env-file ./env/.env --file ./docker-compose-dev.yaml up django_runserver --build --no-deps --force-recreate -d



# 4. Tests

## 4.1 Frontend

### 0 tests (100% do not recommend)
- my mistake was from judging how easy it was to manually test when creating new components on blank pages
- nearly unsustainable towards the final stages
- one small change can now require entire steps of manual tests
- if this project is to be worked on, automated tests must be created first
- refer to Jest/Vitest for unit and component testing
- refer to Playwright/Cypress for UI-heavy flows via end-to-end testing

## 4.2 Backend

### Database Separation for Different Tests
- Django's default testing behaviour is to auto-create test db, then destroy it after the tests
- you can persist the test db, but it's only seamless enough for test-and-check steps
- to solve this, explicitly declare 'TEST' db at settings.dev
- create a custom TestRunner (TestRunnerWithMirror) that will use {'MIRROR': 'default'}
- MIRROR is Django's way of allowing you to use multiple dbs
- writing to a mirrored db will also write to source db
- therefore, making tests use live dev db requires test db to mirror live dev db

You can now populate live dev db permanently, then freely choose when to use it during tests via "--testrunner=...".
```python
#at settings.dev:
DATABASES['default'].update({
    'TEST': {
        #'NAME' does not seem to matter but must be specified
        'NAME': 'test_' + DATABASES['default']['NAME'],
        #no 'MIRROR' key-value here, so we can use flag + custom runner and add 'MIRROR' whenever we want to use main db
    },
})

#at voicewake.tests.test_metrics:
#custom test runner to allow for toggling of "MIRROR" at db
#since TEST_RUNNER cannot be changed via @override_settings, i.e. too late
class TestRunnerWithMirror(DiscoverRunner):
    def setup_databases(self, **kwargs):
        #override DATABASES before test DB setup
        settings.DATABASES['default']['TEST'].update({'MIRROR': 'default'})
        return super().setup_databases(**kwargs)
```



### 4.2.1 Prepare persistent db data for TestRunnerWithMirror
    #this will generate around 150k audio_clip rows per iteration
    #sample_run(max_randomness_iteration_count=1, use_multiprocessing=True, subprocess_count=2)
    python manage.py shell -c "from voicewake.tests.test_metrics import RealisticBulkData; RealisticBulkData.sample_run(1, True, 2);"
    
### 4.2.2 90% test coverage for unit and integration tests
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
<img width="728" height="356" alt="image" src="https://github.com/user-attachments/assets/530e68cf-3722-4f39-9219-28a1fdeead70" />


### 4.2.3 Sub-150ms query time for performance tests
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
- hardcode the final threshold+buffer value once at voicewake.tests.test_metrics.BrowseEvents_TestCase.maximum_time_elapsed_ms
- when final threshold is hit, allow for 2 retries and +50ms buffer to account for PSQL's self-managed data caching
- raise ValueError when threshold is hit again with 0 retries left



# 5. Deployment

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



# 6. Future Improvements
- add automated frontend tests (skipped to save time based on naive early experiences)
- pub/sub with websockets via Django Channels and Redis for proper notification service (skipped to keep the project simpler and appropriate for realistic low-demand contexts)
- migrate db to AWS RDS when it makes financial sense (skipped for learning opportunities and to save cost on a 0-revenue project)
- for race condition of any future high-stakes "create only" operation, have the frontend generate random UUID once to send with request, then save UUID+request in db table, while enforcing UUID column as unique



# 7. Credits

It is with your largely thankless effort that free learning opportunities through open-source software is widely available. Thank you to all the willing replies on StackOverflow, and the hardworking contributors and maintainers of:
- <a href="https://www.djangoproject.com/">Django</a>
- <a href="https://vuejs.org/">Vue</a>
- <a href="https://pinia.vuejs.org/">Pinia</a>
- <a href="https://www.postgresql.org/">PostgreSQL</a>
- <a href="https://www.docker.com/">Docker</a>
- <a href="https://nginx.org/">NGINX</a>
- <a href="https://docs.celeryq.dev/en/v5.4.0/index.html">Celery</a>
- <a href="https://redis.io/">Redis</a>
- <a href="https://pgbackrest.org/">pgBackRest</a>
- <a href="https://github.com/fail2ban/fail2ban">Fail2Ban</a>
- <a href="https://github.com/Akryum/vue-virtual-scroller">vue-virtual-scroller</a>
- <a href="https://animejs.com/">Animejs</a>
- <a href="https://github.com/emmanuelsw/notiwind">Notiwind</a>
- <a href="https://github.com/muaz-khan/RecordRTC">RecordRTC</a>
- <a href="https://github.com/jantimon/remote-web-worker">remote-web-worker</a>
- <a href="https://github.com/flurdy/bad_usernames">bad_usernames</a>

While this project leverages open-source tools, the original logic and architecture contained here are reserved for portfolio review purposes. See the License section below for details.

# 8. License

This project is Source-Available for portfolio review and educational purposes only.

Copyright © 2026 Adrian Chang. All rights reserved.

This code is not released under an open-source license. Unauthorized copying, modification, or redistribution of this software is strictly prohibited. For full details, see the LICENSE.md file.

# 9. Contributions & Forking

This project is maintained as a personal portfolio piece to showcase my engineering process.

While the source code is public for review, I am not currently accepting Pull Requests or entertaining forks for derivative versions.

Thank you for your understanding.






