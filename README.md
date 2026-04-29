# things3export
A script that connects to your local Things 3 sqlite database and dumps the contents in a structure of folders (one for each area) and markdown files (one for each project, one index for each area, and one index at top level) - modeled after NotePlan.

WARNING: This code does not escape stuff very well. Please only use it on a copy of your personal Things database. It's probably possible to craft a malicious database that could write elsewhere on your system. And verify the output before using it for anything important.

Requirements: Python 3 (no dependencies)

1. Find your database according to [this article](https://culturedcode.com/things/support/articles/2982272/) and **copy** it to the folder of this script.
2. Run the script from terminal using `python3 things3export.py`
3. The directory `export_noteplan3` now contains your data!

Caveats:
- Slashes in folder and filenames (for areas and projects) are replaced with " or "
- Spaces in tags are replaced with _
- Repeating is not supported at all, but marked with #repeating_template
- Reminders are not supported
- Deadlines are not supported in NotePlan, so not really brought over
- NotePlan date: If a task is marked as today in Things 3, it will be in NotePlan. If not, if a task has a start date that will be the date of a task. If not, if it has a deadline, that will be the date of the task.
- Someday/maybe tasks are created as checklist items and tagged #someday
- Status (someday/maybe, cancellations, etc) are not supported for projects in NotePlan. Cancelled and completed projects are ignored.
- Nested tags are flattened

## TODO
* Separate reading and writing, so multiple outputs can be supported
* Handle nested tags
* Dump cancelled or completed projects to an archive file instead of ignoring them
* Compare with [things.sh](https://github.com/AlexanderWillner/things.sh) and update database assumptions

## Known bugs
* The starttime and endtime Front matter for projects is wrong. It looks like Things 3 stores this as something else than timestamps?

## Documentation tidbits:

### TMTask
This is the important table, which keeps projects, headings and tasks.
* Type: 0 for task, 1 for project, 2 for heading
* Status: 0 for not done, 1 seems unused, 2 for cancelled, 3 for completed
* Start: 0 for inbox, 1 for available, 2 for some day
* todayIndexReferenceDate if exists, indicates today
