# This is spaghetti-code Python. Start from the bottom :)

# Imports
import sqlite3, os, datetime

# Global variables
dbconn = None
exportdir = None

filtertasks = "trashed=0"

# Helper for making sqlite return dictionary rows
def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

# Convert Things 3 timestamp to NotePlan date string
def timestamp_to_date(timestamp):
    out = datetime.date.fromtimestamp(timestamp)
    out = out.strftime("%Y-%m-%d %H:%M")
    return out

# Send a query to sqlite, and return all rows
def query(querytext):
    dbcursor = dbconn.cursor()
    dbcursor.execute(querytext)
    return dbcursor.fetchall()

# Create a unique filename by adding a number until we find something that doesn't already exist.
def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 1

    while os.path.exists(path):
        path = filename + " (" + str(counter) + ")" + extension
        counter += 1

    return path

# Output frontmatter
def write_frontmatter(f, frontmatter):
    if not frontmatter:
        return
    
    f.write("---\n")
    for key, value in frontmatter.items():
        f.write(f"{key}: {value}\n")
    f.write("---\n")

# Get tags for a task ID
def get_taglist(task):
    output = query(f"SELECT * FROM TMTaskTag INNER JOIN TMTag ON TMTaskTag.tags = TMTag.uuid WHERE TMTaskTag.tasks='{task['uuid']}'")
    tags = ''
    for row in output:
        tags = tags + '#' + row['title'].replace(' ', '_') + ' '
    return tags.rstrip(' ')

# Get, and out, checklist items for a task
def handle_checklist(task, f):
    output = query(f"SELECT * FROM TMChecklistItem WHERE task='{task['uuid']}' ORDER BY \"index\"")
    if len(output) == 0:
        return
    for row in output:
        state = ""
        if row['status'] == 2:
            state = " [-]"
        elif row['status'] == 3:
            state = " [x]"
        f.write(f"+{state} {row['title']}")

# Output a task
def handle_task(task, f):

    taglist = get_taglist(task)

    tasktype = "*"
    if task['start'] == 0:
        taglist = (taglist + " #inbox").lstrip(' ')
    elif task['start'] == 2:
        taglist = (taglist + " #someday").lstrip(' ')
        tasktype = "-"
    if task['status'] == 2:
        tasktype = "- [-]"
    elif task['status'] == 3:
        taglist = (taglist + " @done("+timestamp_to_date(task['stopDate'])+")").lstrip(' ')
        tasktype = "- [x]"

    datestring = ""
    if task['todayIndexReferenceDate'] is not None:
        taglist = (taglist + " #today").lstrip(' ')
        datestring=">today"
    elif task['startDate'] is not None:
        datestring = timestamp_to_date(task['startDate'])
    elif task['deadline'] is not None:
        datestring = timestamp_to_date(task['deadline'])
    if task['rt1_recurrenceRule'] is not None:
        taglist = (taglist + " #repeating_template").lstrip(' ')

    f.write(f"{tasktype} {task['title']} {taglist} {datestring}\n")
    if len(task['notes']) > 0:
        f.write(f"{task['notes']}\n")
    handle_checklist(task, f)

# Output a heading
def handle_heading(heading, f):
    # Things 3 might not support tags for headings, but we do :)
    taglist = get_taglist(heading)
    f.write(f"## {heading['title']}\n")
    f.write(f"{taglist}\n")
    if len(heading['notes']) > 0:
        # Headings don't have notes, but I don't want to assume anything
        f.write(f"{heading['notes']}\n")
    handle_checklist(heading, f)
    output = query(f"SELECT * FROM TMTask WHERE {filtertasks} AND heading='{heading['uuid']}' ORDER BY \"index\", \"type\"")
    for row in output:
        # Headings only contains tasks for now, but I don't want to assume anything
        if row['type'] == 0:
            handle_task(row, f)
        if row['type'] == 1:
            print("Projects under a heading is not supported - ignoring.", row)
        if row['type'] == 2:
            # Heading under a heading? Weird...
            handle_heading(row, f)

# Output a project
def handle_project(project):
    # We do not output finished or cancelled projects
    if project['status'] in (2, 3):
        return
    taglist = get_taglist(project)
    filename = f"{project['title'].replace("/", " or ")}.md"
    # We might have several projects with the same name
    filename = uniquify(filename)
    with open(filename, "w") as f:
        frontmatter = {
            "Title" : project['title'],
            "Created" : timestamp_to_date(project['creationDate'])
        }
        if project['startDate'] is not None:
            frontmatter['Startdate'] = timestamp_to_date(project['startDate'])
        if project['deadline'] is not None:
            frontmatter['Deadline'] = timestamp_to_date(project['deadline'])
        if project['rt1_recurrenceRule'] is not None:
            taglist = (taglist + " #repeating_template").lstrip(' ')
        if project['todayIndexReferenceDate'] is not None:
            taglist = (taglist + " #today").lstrip(' ')
        if project['start'] == 2:
            taglist = (taglist + " #someday").lstrip(' ')
        if project['status'] == 2:
            taglist = (taglist + " #cancelled").lstrip(' ')
        if project['status'] == 3:
            taglist = (taglist + " #completed").lstrip(' ')
        write_frontmatter(f, frontmatter)
        f.write(f"# {project['title']}\n")
        f.write(f"{taglist}\n")
        if len(project['notes']) > 0:
            f.write(project['notes'] + '\n')
        handle_checklist(project, f)
        output = query(f"SELECT * FROM TMTask WHERE {filtertasks} AND project='{project['uuid']}' ORDER BY \"index\", \"type\"")
        for row in output:
            if row['type'] == 0:
                handle_task(row, f)
            if row['type'] == 1:
                print("Subprojects are not supported - ignoring.", row)
            if row['type'] == 2:
                handle_heading(row, f)

# Output an area
def handle_area(area):
    os.mkdir(area['title'])
    os.chdir(area['title'])

    output = query(f"SELECT * FROM TMTaskTag INNER JOIN TMTag ON TMTaskTag.tags = TMTag.uuid WHERE TMTaskTag.tasks='{area['uuid']}'")
    taglist = ''
    for row in output:
        taglist = taglist + '#' + row['title'].replace(' ', '_') + ' '
    taglist = taglist.rstrip(' ')

    # Handle items in area
    output = query(f"SELECT * FROM TMTask WHERE {filtertasks} AND area='{area['uuid']}' ORDER BY \"index\", \"type\"")

    with open (f"{area['title'].replace("/", " or ")}.md", "w") as f:
        f.write(area['title'] + "\n")
        # Only way I can think of tagging an area in NotePlan
        f.write(f"{taglist}\n")       
        for row in output:
            if row['type'] == 0:
                handle_task(row, f)
            if row['type'] == 2:
                # Areas don't really support headings yet, but the data structure does, so let's pretend
                handle_heading(row, f)

    for row in output:
        if row['type'] == 1:
            handle_project(row)
    os.chdir('..')

# Output the Things3 contents
def handle_things():

    # Handle items without area
    output = query(f"SELECT * FROM TMTask WHERE {filtertasks} AND area IS NULL AND project IS NULL AND heading IS NULL ORDER BY \"index\", \"type\"")

    with open ("Main.md", "w") as f:
        for row in output:
            if row['type'] == 0:
                handle_task(row, f)
            if row['type'] == 2:
                print("Heading without area - ignoring.", row)

    for row in output:
        if row['type'] == 1:
            handle_project(row)

    # Handle areas
    output = query('SELECT * FROM TMArea ORDER BY "index"')
    for row in output:
        handle_area(row)

# Set up database
database = "main.sqlite"
dbconn = sqlite3.connect(database)
dbconn.row_factory = dict_factory

# Set up output directory
os.makedirs("export_noteplan3", exist_ok=True)
os.chdir("export_noteplan3")

handle_things()

# Close up
os.chdir('..')
dbconn.close()
