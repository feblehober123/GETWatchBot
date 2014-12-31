#!/usr/bin/python
#This script keeps the bot running, restarts it, and writes error logs when it bugs out.
import logging

try:
	open('errors.log', 'r').close()
except IOError:
	open('errors.log', 'w').close()

logging.basicConfig(level=logging.WARNING, filename='errors.log', filemode = 'a', format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logging.debug('Starting bot')

while True:
	try:
		execfile('main.py')	#wrapper around code
	except Exception:
		logging.exception("Fatal error occured")
		print "ERROR OCURRED! BOT RESTARTING NOW!"
		logging.warning('Restarting bot')
