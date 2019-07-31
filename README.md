# jira-work-logger
- Description: Auto logger for work logs in JIRA which considers tasks that were assigned for user and were in 'doing' or 'verifying' state on selected date.
- Author: pavelterex (pavelterex@gmail.com)

## How it works?
1. Takes dates range specified
2. Determines which of them are actually working days (regarding to weekdays selected in configurator)
3. Process each working day one by one:
   - get already logged time for the day if any (count time logged to non user-assigned tasks as well)
   - get user tasks that were in 'doing' or 'verifying' state on this date
   - calculate needed time to fulfill target time amount specified in configurator
   - process 'daily tasks' if any by explicitly logging time specified for each one of them (if that won't overload target amount of time for the date)
   - if needed time still remains, proceed tasks that were in 'doing' and 'verifying' state by calculating time for each task and logging it to JIRA
   - finally verify that current date has amount of time logged as expected

## How to use it?
1. Launch .exe or execute runner.py
2. Specify JIRA server and credentials, configure dates range, working weekdays and daily tasks (optional)
3. Press Start button
4. Check the logger output to make sure everything goes fine

## Notes
1. If you'd like to use app on regular basis, you may found useful to specify config options in config.yaml just not to type them every time app launches
2. JIRA password is being stored as plain text in config.yaml (at least yet), so it's up to you whether to store it there or not
