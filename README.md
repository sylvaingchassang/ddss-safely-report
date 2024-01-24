# Safely Report

## Overview

Survey participants often feel reluctant to share their true experience because they are worried about potential retaliation in case their responses are identified (e.g., data leakage). This is especially the case for sensitive survey questions such as those asking about sexual harassment in the workplace. As a result, survey administrators (e.g., company management, researchers) often get inaccurate representation of the reality, which makes it hard to devise an appropriate course of action.

`safely-report` is a survey web application that can provide plausible deniability to survey respondents by recording survey responses with noise. For instance, when asking a worker whether they have been harassed by a manager, the application can be set up to record the answer "yes" with a probability of 30% even if the worker responds "no". This makes it nearly impossible to correctly identify which responses (of all those recorded "yes") are truthful reports &mdash; even if the survey results are leaked. Yet, the survey designer can still know the *proportion* and other statistics of truthful reports because the application tracks the number of cases (but not the cases themselves) where noise injection has happened. Consequently, survey participants feel more safe and become more willing to share their true experience, which has been confirmed by a relevant [study](https://www.nber.org/papers/w31011).

## Installation

Currently, `safely-report` runs on Python version `3.9` due to its dependency on [`pyxform`](https://github.com/XLSForm/pyxform/tree/master).

Once a compatible version of Python is available, clone the `safely-report` repo to the desired location:

```bash
cd <PATH-TO-DESIRED-LOCATION>
git clone https://github.com/princeton-ddss/safely-report.git
```

Then, install packages necessary to run `safely-report`:

```bash
pip install -r requirements.txt
```

## Running the Application

Before running the application, define necessary environment variables:

| Name                       | Description                                                              |
| -------------------------- | ------------------------------------------------------------------------ |
| `SECRET_KEY`               | A key to be used for enhancing the security of the Flask application     |
| `ADMIN_PASSWORD`           | Password for the admin user                                              |
| `SQLALCHEMY_DATABASE_URI`  | URI for connecting to a relational database                              |
| `XLSFORM_PATH`             | Path to the XLSForm file specifying the survey                           |
| `RESPONDENT_ROSTER_PATH`   | Path to the CSV file containing survey respondent roster                 |
| `ENUMERATOR_ROSTER_PATH`   | Path to the CSV file containing survey enumerator roster                 |
| `SESSION_LIFETIME`         | Session expiration time in seconds                                       |

Check `.env.test` file for a concrete example.

To synchronize the database schema, run:

```bash
flask db migrate -m "Test"  # NOTE: Unnecessary once stable schema is committed
flask db upgrade
```

Finally, run the following to launch the application:

```bash
flask --app app run
```

If running on a local server, visit `http://127.0.0.1:5000/survey` to access the application.
