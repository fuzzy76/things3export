# things3export
A script that connects to your local Things 3 sqlite database and dumps the contents in an XML structure. Meant more as a demonstration on how to parse the Things 3 database into something that makes sense.

WARNING: This code does not escape stuff very well. Please only use it on a copy of your Things database. And please verify the output before using it for anything important.

Requirements: Python 3

1. Find your database according to [this article](https://culturedcode.com/things/support/articles/2982272/) and **copy** it to the folder of this script.
2. Run the script from terminal using `python3 things3export.py > output.xml`
3. `output.xml` now contains your data!

