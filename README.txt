Schrodinger's Cat
=================

Entry in PyWeek #12  <http://www.pyweek.org/12/>
URL: https://github.com/rozifus/TeamStrong
Team: TeamStrong
Members: rozifus,kburd,jtrain,danaran
License: see LICENSE.txt


Things you need
---------------

pyglet http://ww.pyglet.org/
pymunk http://code.google.com/p/pymunk/ 

Attribution
-----------

We used Tristam MacDonald's SimplUi
http://swiftcoder.wordpress.com/2009/08/17/simplui-1-0-4-released/

Running the Game
----------------

On Windows or Mac OS X, locate the "run_game.pyw" file and double-click it.

Othewise open a terminal / console and "cd" to the game directory and run:

  python run_game.py


How to Play the Game
--------------------

Schrodinger's cat needs to be gently fed kibble (Kibble is dried cat food).

You are the turret and can shoot kibble. 

Use the mouse to aim the turret.
Mouse pointer distance from turret determines power of kibble shot.
Left click to shoot kibble.
Right click to lay a new vortex.

Left meter is your bullets remaining
Right meter is cat hits remaining until you win!

Development notes 
-----------------

Creating a source distribution with::

   python setup.py sdist

You may also generate Windows executables and OS X applications::

   python setup.py py2exe
   python setup.py py2app

Upload files to PyWeek with::

   python pyweek_upload.py

Upload to the Python Package Index with::

   python setup.py register
   python setup.py sdist upload

