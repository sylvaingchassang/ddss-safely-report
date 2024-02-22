# Getting Started

The easiest way to test out `safely-report` is through running a Docker container.

!!! info

    If you do not have Docker installed, please follow instructions
    [here](https://docs.docker.com/get-docker/) to set it up.

Once Docker is available, store the following environment variables in a `.env` file:

```bash
SAFELY_REPORT_SECRET_KEY=devsecret
SAFELY_REPORT_ADMIN_PASSWORD=devpassword
SAFELY_REPORT_DATABASE_URI=sqlite:///dev.sqlite
XLSFORM_PATH=./tests/data/stats4sd_example_xlsform_adapted.xlsx
RESPONDENT_ROSTER_PATH=./tests/data/example_respondent_roster.csv
ENUMERATOR_ROSTER_PATH=./tests/data/example_enumerator_roster.csv
```

Then, run:

```bash
docker run -p 80:80 --env-file=PATH/TO/ENV princetonddss/safely-report:demo
```

where `PATH/TO/ENV` represents the path to the `.env` file
(e.g., `./.env` if the file is in the current location).

If running on a local server, visit `http://0.0.0.0:80` to access the application.

!!! note

    With environment variables set above, you can use `devpassword` to sign in as admin.
