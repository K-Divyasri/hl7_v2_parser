# Hosting your HL7 v2 parser

You built a real thing: a from-scratch HL7 v2 parser that reads the pipe-and-caret
format hospitals have run on for decades and turns it into clean structured data,
segment by segment. Right now it only runs when you type a command on your laptop.
"Hosting" just means putting the pieces somewhere they keep working when your machine
is asleep - and, just as importantly, somewhere you can send a recruiter a link that
says "paste an HL7 message, watch it get parsed."

There are three pieces, and they live in three free places:

1. The **code** lives on GitHub. That is storage plus version history for your files,
   and it is the thing you link to on a CV.
2. A **live interactive demo** lives on Streamlit Community Cloud. Streamlit turns
   your Python into a small web app; Community Cloud hosts it for free and gives you a
   public URL anyone can click. They paste an HL7 message (or load a sample), hit
   Parse, and watch your parser pull structured JSON out of the wall of pipes - no
   install.
3. The **tests** run in GitHub Actions. Every time you push, GitHub spins up a
   temporary Linux box, runs `pytest`, and shows a green check (or a red X) so you -
   and anyone reading your repo - can see the code actually works.

All three are free at this size. You will not put in a credit card.

## Read this first: why it's safe to host this in public, and the one trap

There is no patient data anywhere in this repo. The sample messages are invented by
`hl7lib/generate.py` using the Faker library - random names, random MRNs, random lab
values. Fake people. That is exactly why you can put this on free public hosting.

But this project has a twist the earlier ones did not: **the app parses whatever the
user pastes in.** So the safety rule points at the user, not just the repo:

> Synthetic data only. Real HL7 messages contain real PHI - names, dates of birth,
> medical record numbers, lab results for actual people. Never paste a real HL7
> message into a public app like this one. Free public hosting is not a BAA-covered
> environment (a provider who has signed a contract making themselves legally
> responsible for the data, like a locked-down AWS/GCP/Azure setup). The app itself
> carries a loud banner saying exactly this - keep it there.

Being able to say that sentence out loud is a hiring signal. It tells an interviewer
you understand not just the code but the rules around the data. The same habit shows
up in your `.gitignore`, which keeps generated files out of the repo even though they
are fake - see Step 1.

---

## Step 1 - Put the code on GitHub

GitHub is where the code lives. First you make a local Git repo, then you make an
empty repo on the website, then you connect the two and push.

### 1a. Check Git knows who you are

Only needed once per machine. If you have committed before, skip it.

```powershell
git config --global user.name "Your Name"
git config --global user.email "mathuransada@gmail.com"
```

### 1b. The .gitignore - read this part, it's the one that bites people

In a health-tech project, the cardinal sin is committing data. Synthetic or not, you
want "generated data never goes in Git" to be muscle memory now, so that the day you
touch real PHI you do not even have to think about it. The project already ships a
`.gitignore` at the root. Open it and confirm it contains at least these lines:

```
out/
output/
.env
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ipynb_checkpoints/
```

Why these matter:

- `out/` and `output/` - any messages you generate locally stay on your laptop. The
  repo ships a tiny committed sample under `build_from_scratch/data/sample/` on
  purpose (so the project runs out of the box), but bulk output you generate does not
  go in Git. Clean repo, right habit.
- `.env` - if you ever add a secret, it goes here, and this line keeps it off the
  internet. Git keeps history forever, so a secret committed once is a secret leaked
  forever, even if you "delete" it in a later commit.

One thing to know about this project: it has no secrets and no database. The parser is
pure standard-library Python; the app generates its samples in memory. So unlike
Project 1, there is no `DB_URL` to manage - nothing to put in GitHub Secrets. One less
thing to get wrong.

### 1c. Decide what to push - push the whole project folder

Push the **whole project folder** (`03_hl7_v2_parser/`) as one repo. That way
`hosting/` and `build_from_scratch/` sit together exactly as the app expects: the
Streamlit app reaches from `hosting/streamlit_app/app.py` up two levels and into
`build_from_scratch/` to import your `hl7lib` package.

If you push only `build_from_scratch/` on its own, the Streamlit app will not find the
code and the deploy will fail. So push from the project root.

### 1d. Initialize, stage, commit

From the project root (`03_hl7_v2_parser/`):

```powershell
git init
git add .
git commit -m "Initial commit: HL7 v2 parser + Streamlit demo + hosting"
```

`git add .` stages everything that is not ignored. Now the critical sanity check:

```powershell
git status
```

Confirm you do **not** see `.env`, a `.venv/` folder, or bulk generated messages under
`out/` listed. If a generated file shows up as staged, your `.gitignore` is not
catching it - run `git rm --cached the_file`, fix the ignore rule, and commit again.
Do this before you push, not after.

### 1e. Make the empty repo on github.com

In the browser:

1. Go to github.com, sign in (create the account first if you have not).
2. Top-right, click the **+** then **New repository**.
3. Name it something like `hl7-v2-parser`. Lowercase, hyphens, no spaces.
4. Leave it **Public** - you want recruiters to see it, and public repos get unlimited
   free GitHub Actions minutes.
5. Do **not** check "Add a README", "Add .gitignore", or "Add a license". You want it
   completely empty, otherwise your first push hits a conflict. Leave all boxes off.
6. Click **Create repository**.

GitHub then shows a page with commands. Ignore most of it and use what is below.

### 1f. Connect and push

Copy the repo URL from that page (the
`https://github.com/yourname/hl7-v2-parser.git` one). Then:

```powershell
git remote add origin https://github.com/YOURNAME/hl7-v2-parser.git
git branch -M main
git push -u origin main
```

The first push pops a browser window or a credential prompt to log into GitHub. Do it.
If it asks for a password in the terminal, that will not work anymore - GitHub killed
password auth. Use the browser sign-in it offers, or a Personal Access Token as the
password. The browser flow is easier.

Refresh the GitHub page. Your files are there. The code is hosted. One piece down.

---

## Step 2 - Deploy the live demo to Streamlit Community Cloud

This is the fun part: a public URL where anyone can paste an HL7 message, hit Parse,
and watch your parser turn it into structured JSON and a field-by-field breakdown in
real time. The app file is already written - it is `hosting/streamlit_app/app.py`. It
imports your real `hl7lib` package, gives the visitor "Load sample ADT" and "Load
sample ORU" buttons plus a box to paste their own message, and on Parse shows both the
clean nested JSON and a labelled table for every segment. You just have to point
Streamlit at it.

The official walkthrough is here and worth a skim:
https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started

### 2a. Sign in

1. Go to https://share.streamlit.io and click **Continue with GitHub**.
2. Authorize Streamlit to see your repos. (It needs read access to deploy from them.)

Signing in with the same GitHub account you just pushed to means Streamlit can see your
new repo immediately.

### 2b. Create the app

1. Click **Create app** (sometimes labelled "New app").
2. Choose **Deploy a public app from GitHub** / "Use existing repo".
3. Fill in the three fields:
   - **Repository:** `YOURNAME/hl7-v2-parser`
   - **Branch:** `main`
   - **Main file path:** `hosting/streamlit_app/app.py`

   That main file path is the one people get wrong. It is the path **inside your repo**
   to the app script. Type it exactly: `hosting/streamlit_app/app.py`. If you pushed
   only the `build_from_scratch` folder instead of the whole project, this path will
   not exist and the deploy will fail - that is the reason Step 1 said push from the
   project root.

4. Click **Deploy**.

### 2c. What happens next

Streamlit reads `hosting/streamlit_app/requirements.txt`, installs streamlit and Faker
on its server, then runs your app. (It does not install `hl7lib` - that is your own
code, imported straight from `build_from_scratch/`, and it is pure standard library
with no dependencies.) The first build takes a couple of minutes - you will see a log
scrolling. When it finishes you get a public URL like
`https://your-app-name.streamlit.app`. Open it. Click **Load sample ADT**, then
**Parse message**, and you should see the structured JSON on one side and a labelled
table per segment on the other.

That URL is shareable. Send it to anyone. It is, genuinely, your parser running on the
internet.

### 2d. If the deploy goes red

Click into the log; the real error is usually near the bottom.

- `ModuleNotFoundError: No module named 'hl7lib'` - the repo does not contain
  `build_from_scratch/`, or you deployed from the wrong folder. The app reaches from
  `hosting/streamlit_app/app.py` up two levels and into `build_from_scratch/` to find
  the package. Both folders must be in the same repo. Push from the project root and
  redeploy.
- `ModuleNotFoundError: No module named 'faker'` - a package is missing from
  `hosting/streamlit_app/requirements.txt`. Add it, push, and Streamlit redeploys
  automatically on the next push.
- "main file not found" - the **Main file path** is wrong. It must be
  `hosting/streamlit_app/app.py`, spelled exactly.

Every time you push to `main`, Streamlit redeploys on its own. No need to click
anything after the first time.

---

## Step 3 - Turn on CI (run the tests automatically)

Your `build_from_scratch/` folder has a pytest suite (around 23 tests). Right now those
only run when you type `pytest`. GitHub Actions runs them for you on every push, on
GitHub's machines, for free, and shows a green check on your repo when they pass. That
green check is what turns "I wrote some code" into "I wrote tested code."

### 3a. Put the workflow file in the right place

A workflow only runs if it lives at `.github/workflows/` in your repo. This hosting
folder ships a ready-made one at `hosting/github_actions/tests.yml`. Copy it to the
real location:

```powershell
mkdir .github\workflows
copy hosting\github_actions\tests.yml .github\workflows\tests.yml
```

Then commit and push:

```powershell
git add .github\workflows\tests.yml
git commit -m "Add CI: run pytest on every push"
git push
```

### 3b. What the workflow does

Open the file and read the comments - it is deliberately written to be read. In short,
on every push or pull request (and on demand from the Actions tab) it:

1. Checks out your code onto a fresh Ubuntu box.
2. Installs Python 3.12.
3. Installs `build_from_scratch/requirements.txt` (Faker, pytest).
4. Runs `pytest -v` inside `build_from_scratch/`.

The `working-directory: build_from_scratch` line on the install and test steps is the
important detail: it tells the runner to stand inside that folder, because that is
where the `hl7lib` package and the `tests/` folder live. Run pytest from the repo root
and it would not find them.

If every test passes, the run is green. If one fails, it goes red and GitHub emails you.

### 3c. Watch it run, then add the badge

1. Go to your repo's **Actions** tab. You will see a run already going (the push
   triggered it).
2. Click into it, click the **pytest** job, and watch the steps expand live. Green
   check means it worked. Click any step to read its log.

Now add a **status badge** to your README - the little "Tests: passing" image. It is
the first thing a recruiter's eye lands on. On the Actions page, click your "Tests"
workflow, then the `...` menu, then **Create status badge**, and copy the Markdown. It
looks like this (swap in your username and repo):

```markdown
![Tests](https://github.com/YOURNAME/hl7-v2-parser/actions/workflows/tests.yml/badge.svg)
```

Paste that at the top of your README. Now anyone landing on your repo sees, at a
glance, that the tests pass.

Full Actions docs if you want to go deeper: https://docs.github.com/actions

### 3d. The free-minutes thing, briefly

Public repos get **unlimited** free Actions minutes, so you never have to think about
this. (Private repos get a couple thousand minutes a month, which a test run like this
barely dents.) This workflow runs on push, not on a schedule, so it just runs whenever
you push. Nothing to manage.

---

## What to put in your README and show a recruiter

When you write the repo's README, describe it as what it is: a from-scratch HL7 v2
parser that reads the encoding characters from MSH, splits each segment into fields,
repetitions, components, and subcomponents, and extracts structured patient, visit, and
lab-result data from ADT and ORU messages, with graceful handling of malformed input.
Put these at the top:

- The **tests badge** (Step 3c).
- A link to the **live Streamlit demo**.
- The **synthetic-data sentence** (synthetic data only; never paste real PHI into a
  public app; real HL7 belongs in a BAA-covered environment). This one line does a lot
  of work.

In an interview, the points that land:

- **You understand HL7 v2 down to the delimiters.** You can explain that a message
  declares its own encoding characters in MSH-1 and MSH-2, that segments are separated
  by carriage returns and fields by pipes, and that a field nests into repetitions,
  components, and subcomponents. You wrote the code that reads all of that - you are not
  reciting, you built it.
- **You know the two workhorse message types.** ADT keeps registration and clinical
  systems in sync as a patient is admitted, discharged, or transferred (the trigger
  event is the second component of MSH-9, e.g. `ADT^A01`). ORU carries lab results back,
  with OBX result segments grouped under their OBR order. Your parser handles both.
- **You handle bad input like a professional.** Real feeds are messy. Your parser
  raises a clear `HL7ParseError` on garbage (no MSH, truncated header) and returns empty
  strings rather than crashing on missing fields - and the demo shows a friendly error
  instead of a stack trace. Interviewers care a lot about this.
- **You handle data correctly.** Synthetic only, generated files are gitignored, the
  public app warns users never to paste real PHI, and you know real HL7 needs a
  BAA-covered environment, not free public hosting.
- **It is real and runnable.** There is a live demo a recruiter can click and a CI badge
  proving the tests pass. That is the difference between a toy and a project.

Have the live demo open in a tab during the call. Loading a sample ADT and watching it
resolve into a named patient, a visit, and a labelled breakdown in real time beats any
amount of describing it. And you can add the honest next step: in a real job you would
often reach for a maintained library (hl7apy, python-hl7), and you will understand it
far better for having built one yourself.
