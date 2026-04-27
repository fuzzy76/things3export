import sqlite3, html

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def query(querytext):
    dbcursor = dbconn.cursor()
    dbcursor.execute(querytext)
    return dbcursor.fetchall()

def get_attributelist(row):
    attributes = ''
    for key, value in row.items():
        attributes = attributes + f"{key}=\'{value}\' "
    return attributes.rstrip(' ')

def get_taglist(task):
    output = query(f"SELECT * FROM TMTaskTag INNER JOIN TMTag ON TMTaskTag.tags = TMTag.uuid WHERE TMTaskTag.tasks='{task['uuid']}'")
    tags = ''
    for row in output:
        tags = tags + '"' + row['title'] + '",'
    return tags.rstrip(',')

def handle_checklist(task):
    output = query(f"SELECT * FROM TMChecklistItem WHERE task='{task['uuid']}' ORDER BY \"index\"")
    if len(output) == 0:
        return
    print('<checklist>')
    for row in output:
        attributes = get_attributelist(row)
        print(f"<item {attributes} />")
    print('</checklist>')

def handle_heading(heading):
    attributes = get_attributelist(heading)
    tags = get_taglist(heading)
    print(f"<heading {attributes} tags='{tags}'>")
    # Headings don't have tags, but I don't want to assume anything
    if len(heading['notes']) > 0:
        # Headings don't have notes, but I don't want to assume anything
        print('<note>' + html.escape(heading['notes']) + '</note>')
    handle_checklist(heading)
    output = query(f"SELECT * FROM TMTask WHERE trashed=0 AND heading='{heading['uuid']}' ORDER BY \"index\", \"type\"")
    for row in output:
        # Headings only contains tasks for now, but I don't want to assume anything
        if row['type'] == 0:
            handle_task(row)
        if row['type'] == 1:
            handle_project(row)
        if row['type'] == 2:
            handle_heading(row)
    print('</heading>')

def handle_project(project):
    attributes = get_attributelist(project)
    tags = get_taglist(project)
    print(f"<project {attributes} tags='{tags}'>")
    if len(project['notes']) > 0:
        print('<note>' + html.escape(project['notes']) + '</note>')
    handle_checklist(project)
    output = query(f"SELECT * FROM TMTask WHERE trashed=0 AND project='{project['uuid']}' ORDER BY \"index\", \"type\"")
    for row in output:
        if row['type'] == 0:
            handle_task(row)
        if row['type'] == 1:
            # Subprojects is not really a thing yet, but I don't want to assume anything
            handle_project(row)
        if row['type'] == 2:
            handle_heading(row)
    print('</project>')

def handle_task(task):
    attributes = get_attributelist(task)
    tags = get_taglist(task)
    print(f"<task {attributes} tags='{tags}'>")
    if len(task['notes']) > 0:
        print('<note>' + html.escape(task['notes']) + '</note>')
    handle_checklist(task)
    print('</task>')


def handle_area(area):
    attributes = get_attributelist(area)
    print(f"<area {attributes}>")
    output = query(f"SELECT * FROM TMTask WHERE trashed=0 AND area='{area['uuid']}' ORDER BY \"index\", \"type\"")
    for row in output:
        if row['type'] == 0:
            handle_task(row)
        if row['type'] == 1:
            handle_project(row)
        if row['type'] == 2:
            # Areas don't support headings yet, but I've asked Cultured Code for it :)
            handle_heading(row)
    print('</area>')

def handle_things():
    print('<things3>')
    output = query('SELECT * FROM TMArea ORDER BY "index"')
    for row in output:
        handle_area(row)
    print ('</things3>')


database = "main.sqlite"

# Connecting to sqlite databse
dbconn = sqlite3.connect(database)
dbconn.row_factory = dict_factory

handle_things()

dbconn.commit()

# Close the connection
dbconn.close()


