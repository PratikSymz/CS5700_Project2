scripts=webcrawler
files=main.py

perm:
	chmod 755 $(scripts)
	chmod 755 $(files)

all: perm
	echo "Complete"