program_script=webcrawler
main_program=main.py

perm:
	chmod 755 $(program_script)
	chmod 755 $(main_program)

all: perm