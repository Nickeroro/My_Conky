#!/usr/bin/python
# encoding: utf-8

# Owner: Per Alexandersson, per.w.alexandersson@gmail.com
# Version: 2016-03-09
#
#
# Script for reading google calendars and render them suitable for Conky.
#
# This program requires gcalcli to be installed on the system.
#
# Call from conky conf file like this for example:
# ${execpi 1000 python thisFileName.py }

import sys, os, re
from datetime import datetime, date, time, timedelta
from subprocess import Popen, PIPE


colorDict = {
	'dayName':'#ffffff',
	'pastDate':'#333333',
	'currentDate':'#ffaa33',
	'taskDate':'#ffffff',
	'normalDate':'#999999',
	'weekColor':'#ffffff',
	'taskListTitle':'#ffffff',
	'taskNormal':'#cccccc', 
	'taskMaybe':'#999999', # Tasks ending with '?'
	'taskImportant':'#ffffff', # Tasks ending with '!'
	'lastUpdated':'#ffffff',
	}

# Fonts for various things
calFont = '${font DejaVu Sans Mono:size=14}'
weekcalFont = '${font DejaVu Sans Mono:size=16:Bold}'
taskTitleFont = '${font Vera:size=16}'
taskTimeFont = '${font DejaVu Sans Mono:size=11}'
taskFont = '${font Vera:size=11}'
lastUpdatedFont = '${font Vera:size=8}'
foodFont = '${font Vera:size=8}'


def roundToMidnight(time):
	return time.replace(hour=0,minute=0,second=0,microsecond=0)
	

def tasksFromGoogle():
	
	def toNearestYear(dt):
		now = datetime.now()
		modified = dt.replace(year=now.year)
		
		return modified
	
	start_str = date.today().strftime("%Y-%m-%d")
	#Get events for the coming 40 days
	length = timedelta(days=40)
	end = date.today() + length
	end_str = end.strftime("%Y-%m-%d")
	
	
	p = Popen(['Calendar', '--military', '--nocolor' ,'agenda', start_str,end_str], stdin=PIPE, stdout=PIPE, stderr=PIPE)
	output, err = p.communicate()
	
	eventList = output.split("\n");
	
	dateTaskList=[]
	
	savedDate =  datetime.now()
	
	#Loop over events
	for event in eventList:
		
		if event == "":
			continue
		
		#12345678901234567890
		#Thu Dec 18  10:30  
	
		
		#Extract start time
		try:
			starttime = datetime.strptime(event[0:17], '%a %b %d  %H:%M')
			starttime = toNearestYear(starttime)
			savedDate = starttime
		except ValueError:
			try:
				#only week entries defines the dates
				starttime = datetime.strptime(event[0:12], '%a %b %d      ')
				savedDate = toNearestYear(starttime)
				starttime = starttime.replace(savedDate.year, savedDate.month, savedDate.day ) 
				
				#if event[19:].startswith("Week"):
					#savedDate = toNearestYear(starttime)
					#continue
				
			except ValueError:
				try:
					starttime = datetime.strptime(event[0:17], '            %H:%M')
					starttime = starttime.replace(savedDate.year, savedDate.month, savedDate.day ) 
				except ValueError:
					starttime = savedDate
					
		
		
		if event[19:].startswith("Week"):
			continue
		
		#print event
		#print starttime, event[19:]
		
		
		
		#Extract event description, and add as pair to the list
		dateTaskList.append([ starttime , event[19:] ])
	
	return dateTaskList


#Misc. util functions
def getTaskRange(taskList, startTime, endTime):
	return [task for task in taskList
		if task[0]>=startTime and task[0]<=endTime]

def dayEntry(taskList, date):
		return getTaskRange(taskList, date.replace(hour=0,minute=0,second=0,microsecond=0), date.replace(hour=23,minute=59,second=59,microsecond=999999))

##Formatting Conky functions below
#############################################################

#Prints calendar
def calendarPrint(taskList=[], now=datetime.now().replace(second=0,microsecond=0)):
	
	#Day current week starts at
	weekStart = now + timedelta(days = -now.weekday())
	
	dayAdd = timedelta(days=1)
	
	
	#Print days of week
	print ('   %s${%s}  Mon Tue Wed Thu Fri Sat Sun' % (calFont,colorDict['dayName']))
	
	# Calendar forecast
	for week in range(4):
		for day in range(7):
			theDate = weekStart + (7*week + day)*dayAdd
			
			#Print week number before first day in week
			if day==0:
				theweek = theDate.isocalendar()[1]
				#Need to pad with a space if the week is <10
				if theweek<10:
					print (')%s${%s} %d%s' % (weekcalFont,colorDict['weekColor'],theweek,calFont)),
				else:
					print ('%s${%s}%d%s' % (weekcalFont,colorDict['weekColor'],theweek,calFont)),
			
			
			# Decide on what color to use
			if theDate == now:
				print ('${%s}' % colorDict['currentDate']),
			elif theDate < now:
				print ('${%s}' % colorDict['pastDate']),
			elif len(dayEntry(taskList,theDate))>0:
				print ('${%s}' % colorDict['taskDate']),
			else:
				print ('${%s}' % colorDict['normalDate']),
				
			# Print day of date
			print (str(theDate.day).rjust(2)),
		
		#Newline
		print ('')
	

def getTaskColor(taskString):
	if  taskString[-1] == '!':
		return 'taskImportant'
	elif taskString[-1]=='?':
		return 'taskMaybe'
	else:
		return 'taskNormal'
	
#Print tasks given starttime and timedelta
#Default start is current day, at midnight
def taskRangePrint(tasklist=[], timeStart=roundToMidnight(datetime.now()), timeDelta=timedelta(days=1)):
	
	# Remove 1 microsec, since 00:00:00 + one day, is 00:00:00 next day.
	taskRangeList = getTaskRange(tasklist,timeStart,timeStart+timeDelta-timedelta(microseconds=1))
	
	
	lastDay=None
	sys.stdout.write(taskFont)
	for task in taskRangeList:
		
		# No title tasks are not printed. 
		if task[1] == '':
			continue
		
		taskColor = colorDict[getTaskColor(task[1])]
		
		if task[0].date() == lastDay:
			if task[0].hour==0 and task[0].minute==0:
				print ('${%s}%s%s                             %s' % (taskColor,taskTimeFont, taskFont, task[1]))
			else:
				print ('${%s}%s%s %s%s' % (taskColor,taskTimeFont, task[0].strftime('          %H:%M'),taskFont, task[1]))
				
		else:
			lastDay = task[0].date()
			if task[0].hour==0 and task[0].minute==0:
				print ('${%s}%s%s %s%s' % (taskColor,taskTimeFont, task[0].strftime('%a %d/%m      '),taskFont, task[1]))
			else:
				print ('${%s}%s%s %s%s' % (taskColor,taskTimeFont, task[0].strftime('%a %d/%m %H:%M'),taskFont, task[1]))
				

def tasksTitlePrint(title):
	print ('%s${%s}%s${hr}' % (taskTitleFont,colorDict['taskListTitle'],title))


# Print title + tasks only if there are tasks
def taskTitleRangePrint(taskList, title, start, delta):
	
	if len(getTaskRange(taskList, start, start+delta))>0:
		tasksTitlePrint('\n'+title)
		taskRangePrint(taskList, start, delta)

def todoListTitlePrint(todoList,title):
	if len(todoList)>0:
		tasksTitlePrint('\n'+title)
		
		#Print all todos
		sys.stdout.write(taskFont)
		for todo in todoList:
			print ('${%s}%s' % (colorDict[getTaskColor(todo)], todo))
			

#----------------------------------------------------------------------------------
			

#Fetch the tasks
tasks = tasksFromGoogle()


#Print the calendar
calendarPrint(tasks)


today = roundToMidnight(datetime.now())
dayDelta = timedelta(days=1)

# Print various tasks
taskTitleRangePrint(tasks,'Today ' + datetime.now().strftime('%d %B'), today, dayDelta)

taskTitleRangePrint(tasks,'Tomorrow', today+dayDelta, dayDelta)

taskTitleRangePrint(tasks,'Upcoming', today + 2*dayDelta, 7*dayDelta)

