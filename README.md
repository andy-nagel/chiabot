# chiabot

This script invokes the chia plotter and moves plots to a final directory repeatedly and runs until failure.

Copy this file to the directory where you've installed chia.  Navigate to that directory and activate the env

`. ./activate`

then

`python chiabot.py`

The motivation for not having chia copy the final file directly with `-d` is so if there is a problem
with the transfer, the completed plot won't be corrupted, and you can manually copy later. 

It also writes consolidated logs and stats to the final drive, so if you have multiple machines plotting 
locally and moving to a larger shared drive, you can see the results of all in one place.

When plotting on slow disks, it made sense to do the final copy asynchronously so disk contention
doesn't make it take forever and slow down the plotting, but depending on your system async may work 
for you.

The example provided settings may also need tweaking for your system. 
